from typing import List
from src.model.flow import ExecutionContext, FlowTemplate, Task, TaskDataItem
import pytest

class Task1(Task):
    def inputs(self) -> list[TaskDataItem]:
        return [TaskDataItem("A", int)]
    
    def outputs(self) -> list[TaskDataItem]:
         return [TaskDataItem("B", str)]

class Task2(Task):
    def inputs(self) -> list[TaskDataItem]:
        return [TaskDataItem("C", str)]
    
    def outputs(self) -> list[TaskDataItem]:
         return [TaskDataItem("D", str)]

class Task3(Task):
    def inputs(self) -> list[TaskDataItem]:
        return [TaskDataItem("B", str)]

    def outputs(self) -> list[TaskDataItem]:
        return [TaskDataItem("A", int)]

class TestFlowTemplate():
    subject = None

    @pytest.fixture(autouse=True)
    def before_tests(self):
        self.subject = FlowTemplate("template")
    
    def test_flow_template_with_task_input_data_item_non_existent_in_execution_context(self):
        # Given
        execution_context = ExecutionContext()
        execution_context.set("A", 1)
        
        firstTask = Task1()
        self.subject.add_task(firstTask)

        secondTask = Task2()

        # When/Then
        with pytest.raises(ValueError) as exc:
            self.subject.add_task(secondTask)
        
        raised_exception = exc.value
        assert(type(raised_exception) is ValueError)

    def test_flow_template_with_task_output_data_item_redifining_output(self):
        # Given
        execution_context = ExecutionContext()
        execution_context.set("A", 1)
        
        firstTask = Task1()
        self.subject.add_task(firstTask)

        secondTask = Task3()

        # When/Then
        with pytest.raises(ValueError) as exc:
            self.subject.add_task(secondTask)
        
        raised_exception = exc.value
        assert(type(raised_exception) is ValueError)