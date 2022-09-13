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

class Task:
    def run(self, context: ExecutionContext) -> ExecutionContext:
        pass

class FlowTemplate:
    name: str
    tasks: list[Task]

    def __init__(self, name):
        self.name = name
        self.tasks = []

    def add_task(self, task: Task) -> None:
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