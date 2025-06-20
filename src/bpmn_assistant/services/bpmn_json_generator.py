import xml.etree.ElementTree as ET
from collections import deque
from typing import Any, Optional

from bpmn_assistant.core.enums import BPMNElementType


class BpmnJsonGenerator:
    """
    Class to generate the JSON representation of a BPMN process from the BPMN XML.
    """

    def __init__(self):
        self.elements: dict[str, dict[str, Any]] = {}
        self.flows: dict[str, dict[str, Any]] = {}
        self.process: list[dict[str, Any]] = []

    def _find_process_element(self, root: ET.Element) -> ET.Element:
        for elem in root.iter():
            if elem.tag.endswith("process"):
                return elem
        raise ValueError("No process element found in the BPMN XML")

    def create_bpmn_json(self, bpmn_xml: str) -> list[dict[str, Any]]:
        """
        Create the JSON representation of the process from the BPMN XML
        Constraints:
            - Supported elements: task, userTask, serviceTask, startEvent, endEvent, exclusiveGateway, parallelGateway
            - The process must have only one start event
            - The process must not contain pools or lanes
            - Parallel gateways must have a corresponding join gateway
        """
        root = ET.fromstring(bpmn_xml)
        process_element = self._find_process_element(root)
        self._get_elements_and_flows(process_element)
        self._build_process_structure()
        return self.process

    def _build_process_structure(self):
        start_event = next(
            elem
            for elem in self.elements.values()
            if elem["type"] == BPMNElementType.START_EVENT.value
        )

        # Start building the process structure recursively from the start event
        self.process = self._build_structure_recursive(start_event["id"])

    def _build_structure_recursive(
        self,
        current_id: str,
        stop_at: Optional[str] = None,
        visited: Optional[set] = None,
    ) -> list[dict[str, Any]]:
        if visited is None:
            visited = set()

        if current_id in visited or current_id == stop_at:
            return []

        visited.add(current_id)

        current_element = self.elements[current_id]
        result = [current_element]

        outgoing_flows = self._get_outgoing_flows(current_id)

        if current_element["type"] == BPMNElementType.EXCLUSIVE_GATEWAY.value:
            gateway = current_element.copy()
            gateway["branches"] = []
            gateway["has_join"] = False

            common_branch_endpoint = self._find_common_branch_endpoint(current_id)
            next_element = None

            # If the common endpoint is an exclusive gateway, is means this gateway has a join
            if common_branch_endpoint and self._is_exclusive_gateway(
                common_branch_endpoint
            ):
                gateway["has_join"] = True

                # Retrieve outgoing flows to determine the next element after the join
                join_outgoing_flows = self._get_outgoing_flows(common_branch_endpoint)

                # Validate that the join gateway has exactly one outgoing flow
                if len(join_outgoing_flows) != 1:
                    raise ValueError(
                        "Join gateway should have exactly one outgoing flow"
                    )

                next_element = join_outgoing_flows[0]["target"]
            else:
                next_element = common_branch_endpoint

            # Build the branches of the exclusive gateway
            for flow in outgoing_flows:
                branch_path = self._build_structure_recursive(
                    flow["target"],
                    stop_at=common_branch_endpoint,
                    visited=visited,
                )

                branch = self._build_eg_branch(
                    branch_path, common_branch_endpoint, flow
                )

                gateway["branches"].append(branch)

            result = [gateway]

            # Continue building the structure from the element after the gateway
            if next_element:
                result.extend(
                    self._build_structure_recursive(next_element, stop_at, visited)
                )

        elif current_element["type"] == BPMNElementType.PARALLEL_GATEWAY.value:
            gateway = current_element.copy()
            gateway["branches"] = []

            join_element = self._find_common_branch_endpoint(current_id)

            if (
                not join_element
                or not self._is_parallel_gateway(join_element)
                or len(self._get_outgoing_flows(join_element)) != 1
            ):
                raise ValueError(
                    "Parallel gateway must have a corresponding join gateway"
                )

            # Build the branches of the parallel gateway up to the join gateway
            for flow in outgoing_flows:
                branch = self._build_structure_recursive(
                    flow["target"], stop_at=join_element, visited=visited.copy()
                )
                gateway["branches"].append(branch)

            result = [gateway]

            # Continue building the process from the element after the join gateway
            join_outgoing_flows = self._get_outgoing_flows(join_element)
            next_element = join_outgoing_flows[0]["target"]
            result.extend(
                self._build_structure_recursive(next_element, stop_at, visited)
            )

        elif len(outgoing_flows) == 1:
            next_id = outgoing_flows[0]["target"]
            result.extend(self._build_structure_recursive(next_id, stop_at, visited))

        return result

    def _build_eg_branch(
        self,
        branch_path: list[dict[str, Any]],
        common_branch_endpoint: Optional[str],
        flow: dict[str, str],
    ) -> dict[str, Any]:
        """
        Build the branch structure for an exclusive gateway.
        Args:
            branch_path: The structure of the branch.
            common_branch_endpoint: The ID of the common endpoint for the branches of the gateway.
            flow: The flow object of the branch.
        Returns:
            The branch structure ("condition", "path", "next").
        """
        branch = {
            "condition": flow["condition"],
            "path": branch_path,
        }

        if not branch_path:
            if flow["target"] != common_branch_endpoint:
                branch["next"] = flow["target"]
        else:
            last_element = branch_path[-1]
            last_element_outgoing_flows = self._get_outgoing_flows(last_element["id"])

            if last_element["type"] == BPMNElementType.EXCLUSIVE_GATEWAY.value:
                if not last_element["has_join"]:
                    # We need to add 'next' to each of the branches
                    for sub_branch in last_element["branches"]:
                        sub_flow = next(
                            flow
                            for flow in last_element_outgoing_flows
                            if flow["condition"] == sub_branch["condition"]
                        )
                        sub_branch_result = self._build_eg_branch(
                            sub_branch["path"], common_branch_endpoint, sub_flow
                        )
                        sub_branch.update(sub_branch_result)
                else:
                    join_id = self._find_common_branch_endpoint(last_element["id"])

                    if join_id is None:
                        raise ValueError("Exclusive gateway should have a corresponding join gateway")

                    join_outgoing_flows = self._get_outgoing_flows(join_id)

                    if len(join_outgoing_flows) != 1:
                        raise ValueError("Join gateway should have one outgoing flow")

                    join_target = join_outgoing_flows[0]["target"]
                    if join_target != common_branch_endpoint:
                        branch["next"] = join_target

            elif last_element["type"] == BPMNElementType.PARALLEL_GATEWAY.value:
                join_id = self._find_common_branch_endpoint(last_element["id"])

                if join_id is None:
                    raise ValueError("Parallel gateway should have a corresponding join gateway")

                join_outgoing_flows = self._get_outgoing_flows(join_id)

                if len(join_outgoing_flows) != 1:
                    raise ValueError("Join gateway should have one outgoing flow")

                join_target = join_outgoing_flows[0]["target"]
                if join_target != common_branch_endpoint:
                    branch["next"] = join_target

            elif (
                len(last_element_outgoing_flows) == 1
                and last_element_outgoing_flows[0]["target"] != common_branch_endpoint
            ):
                branch["next"] = last_element_outgoing_flows[0]["target"]

        return branch

    def _is_parallel_gateway(self, gateway_id: str) -> bool:
        return (
            self.elements[gateway_id]["type"] == BPMNElementType.PARALLEL_GATEWAY.value
        )

    def _is_exclusive_gateway(self, gateway_id: str) -> bool:
        return (
            self.elements[gateway_id]["type"] == BPMNElementType.EXCLUSIVE_GATEWAY.value
        )

    def _get_outgoing_flows(self, element_id: str) -> list[dict[str, str]]:
        return [flow for flow in self.flows.values() if flow["source"] == element_id]

    def _find_common_branch_endpoint(self, gateway_id: str) -> Optional[str]:
        """
        Find the common endpoint for the branches of a gateway.
        Args:
            gateway_id: The ID of the gateway element.
        Returns:
            The ID of the common endpoint, or None if no common endpoint is found.
        """
        paths = self._trace_paths(gateway_id)

        for element_id in paths[0]:
            if all(element_id in path for path in paths[1:]):
                return element_id

        return None

    def _trace_paths(self, gateway_id: str) -> list[list[str]]:
        """
        Trace the paths from a given gateway using BFS, constructing an ordered list of elements
        encountered along each outgoing flow. Handles loops by stopping when an element is revisited.
        Args:
            gateway_id: The ID of the gateway element.
        Returns:
           A list of paths, where each path is a list of element IDs.
        """
        paths = []

        # The queue contains the current element, the path taken so far, and the visited elements
        queue = deque([(gateway_id, [gateway_id], {gateway_id})])

        while queue:
            current_id, current_path, visited = queue.popleft()
            outgoing_flows = self._get_outgoing_flows(current_id)

            if not outgoing_flows:
                paths.append(current_path)
                continue

            for flow in outgoing_flows:
                next_id = flow["target"]
                if next_id not in visited:
                    new_path = current_path + [next_id]
                    new_visited = visited.copy()
                    new_visited.add(next_id)
                    queue.append((next_id, new_path, new_visited))
                else:
                    # We've encountered a loop, add this path to the results
                    paths.append(current_path + [next_id])

        # Remove the starting gateway from the paths
        paths = [path[1:] for path in paths]

        return paths

    def _get_elements_and_flows(self, process: ET.Element):
        labeled_elements = {
            BPMNElementType.TASK.value,
            BPMNElementType.USER_TASK.value,
            BPMNElementType.SERVICE_TASK.value,
            BPMNElementType.EXCLUSIVE_GATEWAY.value,
            BPMNElementType.START_EVENT.value,
            BPMNElementType.END_EVENT.value,
        }

        for elem in process:
            tag = elem.tag.split("}")[-1]  # Remove namespace
            elem_id = elem.get("id")

            if tag in [element.value for element in BPMNElementType]:
                self.elements[elem_id] = {
                    "type": tag,
                    "id": elem_id,
                }
                if tag in labeled_elements:
                    name = elem.get("name")
                    if name:  # Only add label if name exists and is not empty
                        self.elements[elem_id]["label"] = name
            elif tag == "sequenceFlow":
                self.flows[elem_id] = {
                    "id": elem_id,
                    "source": elem.get("sourceRef"),
                    "target": elem.get("targetRef"),
                    "condition": elem.get("name"),
                }
