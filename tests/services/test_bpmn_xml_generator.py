from xml.etree import ElementTree as ET

from bpmn_assistant.services import BpmnXmlGenerator


def elements_equal(e1: ET.Element, e2: ET.Element) -> bool:
    """Recursively compares two XML elements, ignoring the order of child elements."""
    if e1.tag != e2.tag:
        print(f"Tags do not match: {e1.tag} != {e2.tag}")
        return False
    if (e1.text or "").strip() != (e2.text or "").strip():
        print(f"Texts do not match in tag {e1.tag}: '{e1.text}' != '{e2.text}'")
        return False
    if e1.attrib != e2.attrib:
        print(f"Attributes do not match in tag {e1.tag}: {e1.attrib} != {e2.attrib}")
        return False
    if len(e1) != len(e2):
        print(
            f"Number of children do not match in tag {e1.tag}: {len(e1)} != {len(e2)}"
        )
        return False

    # Create a list of child elements for e2 to track matched elements
    children2 = list(e2)

    for child1 in e1:
        match_found = False
        for child2 in children2:
            if elements_equal(child1, child2):
                match_found = True
                children2.remove(child2)
                break
        if not match_found:
            print(
                f"No matching element found for {ET.tostring(child1, encoding='unicode')}"
            )
            return False
    return True


class TestBpmnXmlGenerator:

    def test_create_bpmn_xml_parallel(self, procurement_process):
        xml_generator = BpmnXmlGenerator()
        result = xml_generator.create_bpmn_xml(procurement_process)
        expected_xml = '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_1"><process id="Process_1" isExecutable="false"><startEvent id="start1"><outgoing>start1-parallel1</outgoing></startEvent><parallelGateway id="parallel1"><incoming>start1-parallel1</incoming><outgoing>parallel1-task1</outgoing><outgoing>parallel1-task3</outgoing></parallelGateway><parallelGateway id="parallel1-join"><incoming>task2-parallel1-join</incoming><incoming>task4-parallel1-join</incoming><outgoing>parallel1-join-end1</outgoing></parallelGateway><task id="task1" name="Send mail to supplier"><incoming>parallel1-task1</incoming><outgoing>task1-task2</outgoing></task><task id="task2" name="Prepare the documents"><incoming>task1-task2</incoming><outgoing>task2-parallel1-join</outgoing></task><task id="task3" name="Search for the goods"><incoming>parallel1-task3</incoming><outgoing>task3-task4</outgoing></task><task id="task4" name="Pick up the goods"><incoming>task3-task4</incoming><outgoing>task4-parallel1-join</outgoing></task><endEvent id="end1"><incoming>parallel1-join-end1</incoming></endEvent><sequenceFlow id="start1-parallel1" sourceRef="start1" targetRef="parallel1" /><sequenceFlow id="task1-task2" sourceRef="task1" targetRef="task2" /><sequenceFlow id="parallel1-task1" sourceRef="parallel1" targetRef="task1" /><sequenceFlow id="task2-parallel1-join" sourceRef="task2" targetRef="parallel1-join" /><sequenceFlow id="task3-task4" sourceRef="task3" targetRef="task4" /><sequenceFlow id="parallel1-task3" sourceRef="parallel1" targetRef="task3" /><sequenceFlow id="task4-parallel1-join" sourceRef="task4" targetRef="parallel1-join" /><sequenceFlow id="parallel1-join-end1" sourceRef="parallel1-join" targetRef="end1" /></process></definitions>'
        result_tree = ET.ElementTree(ET.fromstring(result))
        expected_tree = ET.ElementTree(ET.fromstring(expected_xml))
        assert elements_equal(result_tree.getroot(), expected_tree.getroot())

    def test_create_bpmn_xml_linear(self, linear_process):
        xml_generator = BpmnXmlGenerator()
        result = xml_generator.create_bpmn_xml(linear_process)
        expected_xml = '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_1"><process id="Process_1" isExecutable="false"><startEvent id="start1"><outgoing>start1-task1</outgoing></startEvent><task id="task1" name="Receive customer inquiry"><incoming>start1-task1</incoming><outgoing>task1-task2</outgoing></task><userTask id="task2" name="Review product catalog"><incoming>task1-task2</incoming><outgoing>task2-task3</outgoing></userTask><task id="task3" name="Prepare quote"><incoming>task2-task3</incoming><outgoing>task3-task4</outgoing></task><serviceTask id="task4" name="Send quote to customer"><incoming>task3-task4</incoming><outgoing>task4-task5</outgoing></serviceTask><task id="task5" name="Follow up with customer"><incoming>task4-task5</incoming><outgoing>task5-end1</outgoing></task><endEvent id="end1"><incoming>task5-end1</incoming></endEvent><sequenceFlow id="start1-task1" sourceRef="start1" targetRef="task1" /><sequenceFlow id="task1-task2" sourceRef="task1" targetRef="task2" /><sequenceFlow id="task2-task3" sourceRef="task2" targetRef="task3" /><sequenceFlow id="task3-task4" sourceRef="task3" targetRef="task4" /><sequenceFlow id="task4-task5" sourceRef="task4" targetRef="task5" /><sequenceFlow id="task5-end1" sourceRef="task5" targetRef="end1" /></process></definitions>'
        result_tree = ET.ElementTree(ET.fromstring(result))
        expected_tree = ET.ElementTree(ET.fromstring(expected_xml))
        assert elements_equal(result_tree.getroot(), expected_tree.getroot())

    def test_create_bpmn_exclusive(self, order_process):
        xml_generator = BpmnXmlGenerator()
        result = xml_generator.create_bpmn_xml(order_process)
        expected_xml = '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_1"><process id="Process_1" isExecutable="false"><startEvent id="start1"><outgoing>start1-task1</outgoing></startEvent><task id="task1" name="Receive order from customer"><incoming>start1-task1</incoming><outgoing>task1-exclusive1</outgoing></task><exclusiveGateway id="exclusive1" name="Product in stock?"><incoming>task1-exclusive1</incoming><outgoing>exclusive1-task2</outgoing><outgoing>exclusive1-exclusive2</outgoing></exclusiveGateway><task id="task2" name="Notify customer that order cannot be fulfilled"><incoming>exclusive1-task2</incoming><outgoing>task2-end1</outgoing></task><exclusiveGateway id="exclusive2" name="Payment succeeds?"><incoming>exclusive1-exclusive2</incoming><outgoing>exclusive2-task3</outgoing><outgoing>exclusive2-task5</outgoing></exclusiveGateway><task id="task3" name="Process order"><incoming>exclusive2-task3</incoming><outgoing>task3-task4</outgoing></task><task id="task4" name="Notify customer that order has been processed"><incoming>task3-task4</incoming><outgoing>task4-end1</outgoing></task><task id="task5" name="Notify customer that order cannot be processed"><incoming>exclusive2-task5</incoming><outgoing>task5-end1</outgoing></task><endEvent id="end1"><incoming>task2-end1</incoming><incoming>task4-end1</incoming><incoming>task5-end1</incoming></endEvent><sequenceFlow id="start1-task1" sourceRef="start1" targetRef="task1" /><sequenceFlow id="task1-exclusive1" sourceRef="task1" targetRef="exclusive1" /><sequenceFlow id="task2-end1" sourceRef="task2" targetRef="end1" /><sequenceFlow id="exclusive1-task2" sourceRef="exclusive1" targetRef="task2" name="Product is out of stock" /><sequenceFlow id="task3-task4" sourceRef="task3" targetRef="task4" /><sequenceFlow id="task4-end1" sourceRef="task4" targetRef="end1" /><sequenceFlow id="exclusive2-task3" sourceRef="exclusive2" targetRef="task3" name="Payment succeeds" /><sequenceFlow id="task5-end1" sourceRef="task5" targetRef="end1" /><sequenceFlow id="exclusive2-task5" sourceRef="exclusive2" targetRef="task5" name="Payment fails" /><sequenceFlow id="exclusive1-exclusive2" sourceRef="exclusive1" targetRef="exclusive2" name="Product is in stock" /></process></definitions>'
        result_tree = ET.ElementTree(ET.fromstring(result))
        expected_tree = ET.ElementTree(ET.fromstring(expected_xml))
        assert elements_equal(result_tree.getroot(), expected_tree.getroot())

    def test_create_bpmn_xml_pg_inside_eg(self, pg_inside_eg_process):
        xml_generator = BpmnXmlGenerator()
        result = xml_generator.create_bpmn_xml(pg_inside_eg_process)
        expected_xml = '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_1"><process id="Process_1" isExecutable="false"><startEvent id="start1"><outgoing>start1-exclusive1</outgoing></startEvent><exclusiveGateway id="exclusive1" name="Exclusive Decision"><incoming>start1-exclusive1</incoming><outgoing>exclusive1-task2</outgoing><outgoing>exclusive1-parallel1</outgoing></exclusiveGateway><exclusiveGateway id="exclusive1-join"><incoming>task2-exclusive1-join</incoming><incoming>parallel1-join-exclusive1-join</incoming><outgoing>exclusive1-join-end1</outgoing></exclusiveGateway><task id="task2" name="Task A"><incoming>exclusive1-task2</incoming><outgoing>task2-exclusive1-join</outgoing></task><parallelGateway id="parallel1"><incoming>exclusive1-parallel1</incoming><outgoing>parallel1-task3</outgoing><outgoing>parallel1-task4</outgoing></parallelGateway><parallelGateway id="parallel1-join"><incoming>task3-parallel1-join</incoming><incoming>task4-parallel1-join</incoming><outgoing>parallel1-join-exclusive1-join</outgoing></parallelGateway><task id="task3" name="Parallel Task 1"><incoming>parallel1-task3</incoming><outgoing>task3-parallel1-join</outgoing></task><task id="task4" name="Parallel Task 2"><incoming>parallel1-task4</incoming><outgoing>task4-parallel1-join</outgoing></task><endEvent id="end1"><incoming>exclusive1-join-end1</incoming></endEvent><sequenceFlow id="start1-exclusive1" sourceRef="start1" targetRef="exclusive1" /><sequenceFlow id="task2-exclusive1-join" sourceRef="task2" targetRef="exclusive1-join" /><sequenceFlow id="exclusive1-task2" sourceRef="exclusive1" targetRef="task2" name="Condition A" /><sequenceFlow id="parallel1-task3" sourceRef="parallel1" targetRef="task3" /><sequenceFlow id="task3-parallel1-join" sourceRef="task3" targetRef="parallel1-join" /><sequenceFlow id="parallel1-task4" sourceRef="parallel1" targetRef="task4" /><sequenceFlow id="task4-parallel1-join" sourceRef="task4" targetRef="parallel1-join" /><sequenceFlow id="parallel1-join-exclusive1-join" sourceRef="parallel1-join" targetRef="exclusive1-join" /><sequenceFlow id="exclusive1-parallel1" sourceRef="exclusive1" targetRef="parallel1" name="Condition B" /><sequenceFlow id="exclusive1-join-end1" sourceRef="exclusive1-join" targetRef="end1" /></process></definitions>'
        result_tree = ET.ElementTree(ET.fromstring(result))
        expected_tree = ET.ElementTree(ET.fromstring(expected_xml))
        assert elements_equal(result_tree.getroot(), expected_tree.getroot())

    def test_create_bpmn_xml_empty_gateway_paths(self, empty_gateway_path_process):
        xml_generator = BpmnXmlGenerator()
        result = xml_generator.create_bpmn_xml(empty_gateway_path_process)
        expected_xml = '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_1"><process id="Process_1" isExecutable="false"><startEvent id="start"><outgoing>start-task1</outgoing></startEvent><task id="task1" name="Perform a simple task"><incoming>start-task1</incoming><outgoing>task1-task2</outgoing></task><task id="task2" name="Perform a second task"><incoming>task1-task2</incoming><outgoing>task2-exclusive1</outgoing></task><exclusiveGateway id="exclusive1" name="Decision Point"><incoming>task2-exclusive1</incoming><outgoing>exclusive1-task3</outgoing><outgoing>exclusive1-end</outgoing></exclusiveGateway><task id="task3" name="Perform a third task"><incoming>exclusive1-task3</incoming><outgoing>task3-end</outgoing></task><endEvent id="end"><incoming>task3-end</incoming><incoming>exclusive1-end</incoming></endEvent><sequenceFlow id="start-task1" sourceRef="start" targetRef="task1" /><sequenceFlow id="task1-task2" sourceRef="task1" targetRef="task2" /><sequenceFlow id="task2-exclusive1" sourceRef="task2" targetRef="exclusive1" /><sequenceFlow id="task3-end" sourceRef="task3" targetRef="end" /><sequenceFlow id="exclusive1-task3" sourceRef="exclusive1" targetRef="task3" name="Condition A" /><sequenceFlow id="exclusive1-end" sourceRef="exclusive1" targetRef="end" name="Condition B" /></process></definitions>'
        result_tree = ET.ElementTree(ET.fromstring(result))
        expected_tree = ET.ElementTree(ET.fromstring(expected_xml))
        assert elements_equal(result_tree.getroot(), expected_tree.getroot())

    def test_create_bpmn_xml_labeled_events(self, labeled_events_process):
        xml_generator = BpmnXmlGenerator()
        result = xml_generator.create_bpmn_xml(labeled_events_process)
        expected_xml = '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_1"><process id="Process_1" isExecutable="false"><startEvent id="start1" name="Order received"><outgoing>start1-task1</outgoing></startEvent><task id="task1" name="Process order"><incoming>start1-task1</incoming><outgoing>task1-end1</outgoing></task><endEvent id="end1" name="Order completed"><incoming>task1-end1</incoming></endEvent><sequenceFlow id="start1-task1" sourceRef="start1" targetRef="task1" /><sequenceFlow id="task1-end1" sourceRef="task1" targetRef="end1" /></process></definitions>'
        result_tree = ET.ElementTree(ET.fromstring(result))
        expected_tree = ET.ElementTree(ET.fromstring(expected_xml))
        assert elements_equal(result_tree.getroot(), expected_tree.getroot())
