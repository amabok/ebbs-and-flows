from src.model.flow import ExecutionContext, FlowExecution, FlowStatus, FlowTemplate, Task, TaskExecution, TaskStatus
from src.services import flow_service

class FlowRunner:
    flow_templates: list[FlowTemplate]

    def __init__(self, flow_service: flow_service.FlowService):
        self.flow_templates = {}
        self.flow_service = flow_service

    def register_flow_template(self, flow_template: FlowTemplate) -> None:
        flow_name = flow_template.name

        if flow_name in self.flow_templates:
            raise ValueError(f"Flow with name {flow_name} is already registered.")

        self.flow_templates[flow_name] = flow_template

    def get_flow_template(self, flow_name: str) -> FlowTemplate:
        return self.flow_templates[flow_name]

    def schedule_flow(self, flow_template_name: str, execution_context: ExecutionContext) -> int:
        flow_template = self.get_flow_template(flow_template_name)

        if len(flow_template.tasks) == 0:
            raise ValueError("Flow template has no tasks!")

        flow_execution = self.flow_service.create_flow_execution(flow_template.name, execution_context)
        self.flow_service.update_flow_status(flow_execution.execution_id, FlowStatus.SCHEDULED, execution_context)

        return flow_execution.execution_id

    def run_flow(self, strategy: FlowStatus) -> None:
        candidate_flow = self.flow_service.get_runnable_flow(strategy)

        target_flow_status = FlowStatus.RUNNING
        running_flow = self.flow_service.update_flow_status(candidate_flow.execution_id, target_flow_status, candidate_flow.execution_context)

        task = self.get_current_task(running_flow)
        can_run = (task != None)
        while(can_run and target_flow_status == FlowStatus.RUNNING):
            self.flow_service.create_task_execution(running_flow)
            (post_task_execution,output_execution_context) = self.run_task(running_flow, task)
            
            if (post_task_execution.status == TaskStatus.FAILED):
                target_flow_status = FlowStatus.FAILED
                can_run = False
                
            if (post_task_execution.status == TaskStatus.SUCCEEDED):
                target_flow_status = FlowStatus.RUNNING
                can_run = True

            # Check if flow is over
            next_task = self.get_next_task(running_flow)
            if(next_task is None and target_flow_status == FlowStatus.RUNNING):
                target_flow_status = FlowStatus.SUCCEEDED
            else:
                task = next_task
            
            self.flow_service.update_task_execution(running_flow.execution_id, post_task_execution)
            running_flow = self.flow_service.update_flow_status(running_flow.execution_id, target_flow_status, output_execution_context)

    def reschedule_flow_execution(self,flow_execution_id: int) -> None:
        self.flow_service.update_flow_status(flow_execution_id, FlowStatus.RESCHEDULED, None)
    
    def re_run_flow(self) -> None:
        self.run_flow(FlowStatus.RESCHEDULED)

    """ 
    TASKS 
    """
    def get_current_task(self, flow: FlowExecution) -> Task:
        flow_template = self.get_flow_template(flow.template_name)
        task_index = flow.current_task_index
        return flow_template.get_task(task_index)

    def get_next_task(self, flow: FlowExecution) -> Task:
        flow_template = self.get_flow_template(flow.template_name)
        task_index = flow.current_task_index + 1
        return flow_template.get_task(task_index)

    def run_task(self, flow: FlowExecution, task: TaskExecution) -> tuple[TaskExecution, ExecutionContext]:
        input_execution_context = flow.execution_context
        output_execution_context = None

        output =  None
        try:
            output_execution_context = task.run(input_execution_context)
        except Exception:
            # TODO - catch the exception message
            output = "EXCEPTION MESSAGE - TODO"
        
        #TODO: support a case for miss-behaved Task() subclasses that don't return
        task_status = TaskStatus.FAILED if output is not None else TaskStatus.SUCCEEDED

        te = TaskExecution()
        te.flow_execution_id = flow.execution_id
        te.flow_execution_step = flow.execution_step
        te.status = task_status
        te.output = output
        
        return (te, output_execution_context)

default_instance = FlowRunner(flow_service.default_persistent_instance)