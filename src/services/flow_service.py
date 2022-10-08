import copy
import time
from src.model.flow import ExecutionContext, FlowExecution, FlowStatus, PersistenceMode, TaskExecution, TaskStatus
from src.repositories import flow_repository

class FlowService:
    flow_repository = None
    
    allowed_flow_transitions = {
        FlowStatus.CREATED: [FlowStatus.SCHEDULED],
        FlowStatus.SCHEDULED: [FlowStatus.RUNNING],
        FlowStatus.RUNNING: [FlowStatus.RUNNING, FlowStatus.FAILED, FlowStatus.SUCCEEDED],
        FlowStatus.FAILED: [FlowStatus.RESCHEDULED],
        FlowStatus.RESCHEDULED: [FlowStatus.RUNNING]
    }

    def __init__(self, persistence: PersistenceMode):
        if(persistence is PersistenceMode.PERSISTENT):
            self.flow_repository = flow_repository.default_persistent_instance
        else:
            self.flow_repository = flow_repository.FlowRepository.from_persistence_mode(persistence)

    """
    FLOWS
    """
    def create_flow_execution(self, template_name: str, execution_context: ExecutionContext) -> FlowExecution:
        flow_execution = FlowExecution()
        flow_execution.status = FlowStatus.CREATED
        flow_execution.template_name = template_name
        flow_execution.execution_id = self.generate_flow_execution_id()
        flow_execution.execution_context = copy.copy(execution_context)
        flow_execution.timestamp = time.time()

        db_flow_execution = self.flow_repository.save_flow(flow_execution)

        return db_flow_execution

    def generate_flow_execution_id(self) -> int:
        return self.flow_repository.get_max_flow_execution_id()

    def get_flow_execution(self, flow_execution_id: int) -> FlowExecution:
        flow = self.flow_repository.get_flow(flow_execution_id)
        if(flow is None):
            raise ValueError(f"Flow with id {flow_execution_id} does not exist!")

        return flow

    def get_runnable_flow(self, strategy: FlowStatus) -> FlowExecution:
        if(strategy != FlowStatus.SCHEDULED and strategy != FlowStatus.RESCHEDULED):
            raise ValueError(f"Provided '{strategy}' is invalid for getting a runnable flow. Only '{FlowStatus.SCHEDULED}' and '{FlowStatus.RESCHEDULED}' FlowStatuses can be run.")

        return self.flow_repository.get_run_candidate_flow(strategy)

    def update_flow_status(self, flow_id, target_flow_status: FlowStatus, execution_context: ExecutionContext) -> FlowExecution:
        flow_execution = self.flow_repository.get_flow(flow_id)
        origin_flow_status = flow_execution.status

        allowed_targets = self.allowed_flow_transitions.get(origin_flow_status)

        if allowed_targets is None:
            raise ValueError(f"There are no target flows defined for '{origin_flow_status}'")

        if target_flow_status not in allowed_targets:
            raise ValueError(f"Flow transition from '{origin_flow_status}' to '{target_flow_status}' is not allowed!")

        new_flow_execution = copy.copy(flow_execution)
        new_flow_execution.status = target_flow_status
        new_flow_execution.timestamp = time.time()

        # Update the execution_context
        if ( 
            (origin_flow_status == FlowStatus.CREATED and target_flow_status == FlowStatus.SCHEDULED) or
            (origin_flow_status == FlowStatus.SCHEDULED and target_flow_status == FlowStatus.RUNNING) or
            (origin_flow_status == FlowStatus.RUNNING and target_flow_status == FlowStatus.FAILED) or
            (origin_flow_status == FlowStatus.FAILED and target_flow_status == FlowStatus.RESCHEDULED) ):
            new_flow_execution.execution_context = flow_execution.execution_context
        else:
            new_flow_execution.execution_context = execution_context

        # Update the execution step
        if (target_flow_status != FlowStatus.CREATED):
            new_flow_execution.execution_step = flow_execution.execution_step + 1
        
        # Update the current Task Index
        if(target_flow_status == FlowStatus.RUNNING):
            if(origin_flow_status == FlowStatus.RESCHEDULED):
                new_flow_execution.current_task_index = flow_execution.current_task_index
            else:
                new_flow_execution.current_task_index = flow_execution.current_task_index + 1
        
        return self.flow_repository.save_flow(new_flow_execution)

    """
    TASKS
    """
    #TODO: support task class name
    def create_task_execution(self,  flow: FlowExecution) -> TaskExecution:
        flow_execution = self.get_flow_execution(flow.execution_id)
       
        task_execution = TaskExecution()
        task_execution.flow_execution_id = flow.execution_id
        task_execution.flow_execution_step = flow.execution_step
        task_execution.status = TaskStatus.RUNNING
        task_execution.output = None
        task_execution.timestamp = time.time()

        db_task_execution = self.flow_repository.save_task(task_execution)
        return db_task_execution
    
    #TODO: support task class name, check transitions and matching of the flow execution steps with the passed task
    def update_task_execution(self, flow_execution_id: int, task: TaskExecution) -> TaskExecution:
        flow: FlowExecution = self.flow_repository.get_flow(flow_execution_id)
        task.timestamp = time.time()

        if(flow.status != FlowStatus.RUNNING):
            raise ValueError(f"Can't update a Task status on flow {flow.execution_id} because it's status is {flow.status} when it should be {FlowStatus.RUNNING}")

        if(flow.execution_step != task.flow_execution_step):
            raise ValueError(f"Flow execution step ({flow.execution_step}) and task execution flow step ({task.flow_execution_step}) do not match.")

        return self.flow_repository.save_task(task)

    def get_flow_task_execution_history(self, flow_execution_id: int) -> list[TaskExecution]:
        flow = self.get_flow_execution(flow_execution_id)
        return self.flow_repository.get_flow_task_execution_history(flow_execution_id)

default_persistent_instance = FlowService(PersistenceMode.PERSISTENT)