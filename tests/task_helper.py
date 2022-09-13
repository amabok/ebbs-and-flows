from multiprocessing.sharedctypes import Value
from model.flow import ExecutionContext, TaskStatus

class SuccessfulTask:
    def run(self, execution_context: ExecutionContext) -> ExecutionContext:
        ec = ExecutionContext() 
        ec.set("some_output", "OK")
        return ec

class FailingTask:
    def run(self, execution_context: ExecutionContext) -> ExecutionContext:
        raise ValueError("Oh nooo!")

class RoundRobinTask:
    run_count: int
    initial_task_status: TaskStatus
    reverse: dict

    def __init__(self,initial_task_status: TaskStatus) -> None:
        self.run_count = 0
        self.initial_task_status = initial_task_status
        self.reverse = { 
            TaskStatus.SUCCEEDED : TaskStatus.FAILED,
            TaskStatus.FAILED: TaskStatus.SUCCEEDED
        }
        
    def run(self, execution_context: ExecutionContext) -> ExecutionContext:
        target: TaskStatus = None
        if(self.run_count % 2 == 0):
            target = self.initial_task_status
        else:
            target = self.reverse[self.initial_task_status] 
        self.run_count +=1

        if(target is TaskStatus.FAILED):
            raise ValueError("I will fail")
        else:
            ec = ExecutionContext()
            ec.set("some_output","OK")
            return ec