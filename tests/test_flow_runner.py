from src.model.flow import ExecutionContext, FlowStatus, FlowTemplate, PersistenceMode, Task, TaskStatus
from src.runner.flow_runner import FlowRunner
from src.services.flow_service import FlowService
import pytest

from tests.task_helper import FailingTask, SuccessfulTask
from tests.test_helper import TestHelper

class TestRunner:
    subject = None
    flow_service = None

    @pytest.fixture(autouse=True)
    def before_tests(self):
        self.flow_service = FlowService(PersistenceMode.TRANSIENT)
        self.subject = FlowRunner(self.flow_service)

    def test_register_flow(self):
        # Given
        flow_name = "template"
        flow_template = FlowTemplate(flow_name)
        flow_template.add_task(Task())

        # When
        self.subject.register_flow_template(flow_template)

        # Then
        registered_flow = self.subject.get_flow_template(flow_name)
        assert(registered_flow == flow_template)

    def test_schedule_flow(self):
        # Given
        flow_template = FlowTemplate("template")
        flow_template.add_task(Task())

        self.subject.register_flow_template(flow_template)

        context = ExecutionContext()
        
        # When        
        flow_id = self.subject.schedule_flow("template", context)

        # Then
        flow_execution = self.flow_service.get_flow_execution(flow_id)
        assert(flow_execution.status == FlowStatus.SCHEDULED)
    
    def test_run_simple_successful_flow(self):
        # Given
        flow_template = FlowTemplate("template")
        flow_template.add_task(SuccessfulTask())

        self.subject.register_flow_template(flow_template)

        context = ExecutionContext()
        flow_id = self.subject.schedule_flow("template", context)

        # When
        self.subject.run_flow(FlowStatus.SCHEDULED)

        # Then
        flow = self.flow_service.get_flow_execution(flow_id)
        assert(flow.status == FlowStatus.SUCCEEDED)

        flow_task_execution_history = self.flow_service.get_flow_task_execution_history(flow_id)
        assert(len(flow_task_execution_history) == 2)
        
        task_execution = flow_task_execution_history[1]
        assert(task_execution.flow_execution_id == flow_id)
        assert(task_execution.status == TaskStatus.SUCCEEDED)
    
    def test_run_simple_failing_flow(self):
        # Given
        flow_template = FlowTemplate("template")
        flow_template.add_task(FailingTask())

        self.subject.register_flow_template(flow_template)

        context = ExecutionContext()
        flow_id = self.subject.schedule_flow("template", context)

        # When
        self.subject.run_flow(FlowStatus.SCHEDULED)

        # Then
        flow = self.flow_service.get_flow_execution(flow_id)
        assert(flow.status == FlowStatus.FAILED)

        flow_task_execution_history = self.flow_service.get_flow_task_execution_history(flow_id)
        assert(len(flow_task_execution_history) == 2)
        
        task_execution = flow_task_execution_history[1]
        assert(task_execution.flow_execution_id == flow_id)
        assert(task_execution.status == TaskStatus.FAILED)
        assert(task_execution.output == "EXCEPTION MESSAGE - TODO")
    
    def test_run_long_failing_flow(self):
        # Given
        flow_template = TestHelper.create_long_failing_flow()
        
        self.subject.register_flow_template(flow_template)

        context = ExecutionContext()
        flow_id = self.subject.schedule_flow("template", context)

        # When
        self.subject.run_flow(FlowStatus.SCHEDULED)

        # Then
        flow = self.flow_service.get_flow_execution(flow_id)
        assert(flow.status == FlowStatus.FAILED)

        flow_task_execution_history = self.flow_service.get_flow_task_execution_history(flow_id)
        assert(len(flow_task_execution_history) == 4)

        task_execution_0 = flow_task_execution_history[0]
        assert(task_execution_0.flow_execution_id == flow_id)
        assert(task_execution_0.status == TaskStatus.RUNNING)
        assert(task_execution_0.output is None)

        task_execution_1 = flow_task_execution_history[1]
        assert(task_execution_1.flow_execution_id == flow_id)
        assert(task_execution_1.status == TaskStatus.SUCCEEDED)
        assert(task_execution_1.output is None)

        task_execution_2 = flow_task_execution_history[2]
        assert(task_execution_2.flow_execution_id == flow_id)
        assert(task_execution_2.status == TaskStatus.RUNNING)
        assert(task_execution_2.output is None)

        task_execution_3 = flow_task_execution_history[3]
        assert(task_execution_3.flow_execution_id == flow_id)
        assert(task_execution_3.status == TaskStatus.FAILED)
        assert(task_execution_3.output == "EXCEPTION MESSAGE - TODO")
    
    def test_re_run_failed_flow(self):
        # Given
        flow_template = TestHelper.create_long_failing_flow()
        flow_execution_id = TestHelper.run_flow(self.subject, flow_template)

        flow = self.flow_service.get_flow_execution(flow_execution_id)
        assert(flow.status == FlowStatus.FAILED)
        
        flow_task_execution_history = self.flow_service.get_flow_task_execution_history(flow_execution_id)
        assert(len(flow_task_execution_history) == 4)

        self.subject.reschedule_flow_execution(flow_execution_id)
        flow = self.flow_service.get_flow_execution(flow_execution_id)
        assert(flow.status == FlowStatus.RESCHEDULED)

        # When
        self.subject.re_run_flow()
        
        # Then
        flow = self.flow_service.get_flow_execution(flow_execution_id)
        assert(flow.status == FlowStatus.SUCCEEDED)

        flow_task_execution_history = self.flow_service.get_flow_task_execution_history(flow_execution_id)
        assert(len(flow_task_execution_history) == 8)

        task_execution_4 = flow_task_execution_history[4]
        assert(task_execution_4.flow_execution_id == flow_execution_id)
        assert(task_execution_4.status == TaskStatus.RUNNING)
        assert(task_execution_4.output is None)

        task_execution_5 = flow_task_execution_history[5]
        assert(task_execution_5.flow_execution_id == flow_execution_id)
        assert(task_execution_5.status == TaskStatus.SUCCEEDED)
        assert(task_execution_5.output is None)

        task_execution_6 = flow_task_execution_history[6]
        assert(task_execution_6.flow_execution_id == flow_execution_id)
        assert(task_execution_6.status == TaskStatus.RUNNING)
        assert(task_execution_6.output is None)

        task_execution_7 = flow_task_execution_history[7]
        assert(task_execution_7.flow_execution_id == flow_execution_id)
        assert(task_execution_7.status == TaskStatus.SUCCEEDED)
        assert(task_execution_7.output is None)