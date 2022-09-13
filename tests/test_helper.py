from model.flow import ExecutionContext, FlowStatus, FlowTemplate, TaskStatus
from runner.flow_runner import FlowRunner
from tests.task_helper import FailingTask, RoundRobinTask, SuccessfulTask

class TestHelper():

    @staticmethod
    def create_long_failing_flow() -> FlowTemplate:
        flow_template = FlowTemplate("template")
        flow_template.add_task(SuccessfulTask())
        flow_template.add_task(RoundRobinTask(TaskStatus.FAILED))
        flow_template.add_task(SuccessfulTask())
        
        return flow_template

    @staticmethod
    def run_flow(fr:FlowRunner, flow_template: FlowTemplate)-> int:
        fr.register_flow_template(flow_template)

        context = ExecutionContext()
        flow_id = fr.schedule_flow("template", context)

        fr.run_flow(FlowStatus.SCHEDULED)

        return flow_id