from datetime import datetime
from enum import Enum
import json

class PersistenceMode(Enum):
    TRANSIENT = 0,
    PERSISTENT = 1

class ExecutionContext:
    context: dict

    def __init__(self):
        self.context = {}

    def set(self, key: str, value) -> None:
        self.context[key] = value

    def get(self, key: str):
        return self.context[key]

    def to_json(self) -> str:
        return json.dumps(self.context)

    """ 
        Returns a new instance of an ExecutionContext from a Json String representation
    """
    @staticmethod
    def from_json(input_str: str):
        ec = ExecutionContext()
        ec.context = json.loads(input_str)
        
        return ec  

class FlowStatus(Enum):
    CREATED = 0
    SCHEDULED = 1
    RUNNING = 2
    FAILED = 3
    SUCCEEDED = 4
    RESCHEDULED = 5

class TaskStatus(Enum):
    RUNNING = 1
    FAILED = 2
    SUCCEEDED = 3

class TaskDataItem():
    key: str = None
    type: type = None

    def __init__(self, key:str, typ: type):
        self.key = key
        self.typ = typ
    
    def __eq__(self, __o: object) -> bool:
        return type(__o) == type(self) and self.key == __o.key and self.typ == __o.typ

    def __repr__(self) -> str:
        return f"'{self.key}',{self.typ}"

#TODO: How to make it an abstract class so that we can enforce method implementation
class Task:
    def run(self, context: ExecutionContext) -> ExecutionContext:
        return ExecutionContext()

    def inputs(self) -> list[TaskDataItem]:
        return []

    def outputs(self) -> list[TaskDataItem]:
        return []

class FlowTemplateIntegrityChecker:
    tasks: list[Task]
    task_data_items: list[TaskDataItem]
    
    def __init__(self, tasks: list[Task]):
        self.tasks = tasks
        self.task_data_items = []

    #TODO: implement and call before run
    def verify_can_be_started(self, start_execution_context: ExecutionContext) ->bool:
        return False
    
    def verify_tasks_integrity(self, task: Task) -> bool:
        # If we are the first task we add all of the items
        if(len(self.tasks) == 0):
            for input_item in task.inputs():
                self.task_data_items.append(input_item)

        # If we aren't the first task we are going to check if we have our inputs in the current 'bag' of task_data_items
        # AKA: can_task_be_run
        if(len(self.tasks) > 0):
            for input_item in task.inputs():
                if(input_item not in self.task_data_items):
                    raise ValueError(f"Task {task} input {input_item} can't be sourced in the current flow")

            # We are going to check if we re-define/overwrite any of the input or outputs of another previous task
            # AKA: does_start_redefine_input_outputs
            for output_item in task.outputs():
                if(output_item in self.task_data_items):
                    raise ValueError(f"Task {task} input {output_item} re-defines one existing Flow Data input or output data_item")

        # Add outputs to the 'bag' of task_data_items
        for output_item in task.outputs():
                self.task_data_items.append(output_item)

        return True

class FlowTemplate:
    name: str
    tasks: list[Task]

    integrity_checker: FlowTemplateIntegrityChecker

    def __init__(self, name):
        self.name = name
        self.tasks = []

        self.integrity_checker = FlowTemplateIntegrityChecker(self.tasks)
        
    #TODO: also verify if the outputs match/re-define any of the inputs
    def add_task(self, task: Task) -> None:
        self.integrity_checker.verify_tasks_integrity(task)
        self.tasks.append(task)

    def get_task(self, index: int) -> Task:
        if(index == len(self.tasks)):
            return None

        return self.tasks[index]

class TaskExecution:
    flow_execution_id: int
    flow_execution_step: int
    name: str
    status: TaskStatus
    output: str
    timestamp: float

    def __init__(self):
        self.flow_execution_id = None
        self.flow_execution_step = None
        self.name = None
        self.status = None
        self.output = None
        self.timestamp = None
    
    def __repr__(self) -> str:
        return f"{self.flow_execution_id} - {self.flow_execution_step} - {self.name} - '{self.output}' - '{self.status}' - {datetime.fromtimestamp(self.timestamp, tz= None)}"

class FlowExecution:
    execution_id: int
    template_name: str
    status: FlowStatus
    execution_step: int
    current_task_index: int
    execution_context: ExecutionContext
    timestamp: float
         
    def __init__(self):
        self.template_name = "" 
        self.execution_id = -1
        self.execution_step = 0
        self.status = None
        self.current_task_index = -1
        self.execution_context = ExecutionContext()
        self.timestamp = None

    def __repr__(self) -> str:
        return f"{self.template_name} - {self.execution_id} - {self.execution_step} - {self.current_task_index} - '{self.status}' - {datetime.fromtimestamp(self.timestamp, tz= None)}"