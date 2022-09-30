from re import S
from sqlite3 import Error
import sqlite3

from model.flow import ExecutionContext, FlowExecution, FlowStatus, PersistenceMode, TaskExecution, TaskStatus

class FlowRepository:
    current_db_name = None
    db_names = {
        PersistenceMode.TRANSIENT : ":memory:",
        PersistenceMode.PERSISTENT : "flow_store.db"
    }

    connection = None

    """
    SCHEMA CREATION QUERIES
    """
    create_flow_table_query = """
                                CREATE TABLE IF NOT EXISTS flow_executions(
                                        execution_id integer NOT NULL,
                                        execution_step integer NOT NULL,
                                        status text,
                                        template_name text,
                                        current_task_index integer,
                                        execution_context text,
                                        timestamp integer,
                                        PRIMARY KEY(execution_id, execution_step)
                                        )
                                """
    create_task_table_query = """
                              CREATE TABLE IF NOT EXISTS task_executions(
                                        flow_execution_id integer,
                                        flow_execution_step integer,
                                        status text,
                                        output text,
                                        timestamp integer,
                                        FOREIGN KEY (flow_execution_id, flow_execution_step) REFERENCES flow_executions(execution_id, execution_step)
                              )
                              """
    
    """
    FLOW QUERIES
    """
    select_current_execution_id_query = """
                           SELECT MAX(execution_id)
                           FROM flow_executions
                           """
    
    insert_flow_query = """
                        INSERT INTO flow_executions(execution_id, execution_step, status, template_name, current_task_index, execution_context, timestamp)
                        VALUES (?,?,?,?,?,?,?) RETURNING *;
                        """

    select_get_flow_query = """
                    WITH max_row_id AS (SELECT MAX(rowid) AS max FROM flow_executions WHERE execution_id = ?)
                    SELECT * FROM flow_executions, max_row_id WHERE rowid = max_row_id.max
                    """

    select_get_candidate_flow_id = """
                    WITH min_row_id AS (SELECT MIN(rowid) AS min FROM flow_executions WHERE status = ?)
                    SELECT * FROM flow_executions, min_row_id WHERE rowid = min_row_id.min
                    """
    delete_all_flow_data_query = """
                    DELETE FROM flow_executions
                    """

    """
    TASK QUERIES
    """
    insert_task_query = """
                    INSERT INTO task_executions(flow_execution_id, flow_execution_step, status, output, timestamp)
                        VALUES (?,?,?,?,?) RETURNING *;
                    """

    select_flow_task_execution_history_query = """
                    SELECT * FROM task_executions WHERE flow_execution_id = ? ORDER BY rowid
                    """
    
    delete_all_task_data_query = """
                    DELETE FROM task_executions
                    """

    def __init__(self, persistence_mode: PersistenceMode):
        try:
            self.current_db_name = self.db_names.get(persistence_mode)
            
            if(self.current_db_name is None):
                raise ValueError(f"There is no configured database name for ${persistence_mode} persistence mode")

            self.connection = sqlite3.connect(self.current_db_name)
            self.create_schema()
        except Error as error:
            raise Exception("Error connecting to database")
    
    def refresh(self):
        try:
            self.connection = sqlite3.connect(self.current_db_name)
        except Error as error:
            raise Exception("Error refreshing connection")

    #TODO substitute for a proper sql file load
    def create_schema(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute(self.create_flow_table_query)
            cursor.execute(self.create_task_table_query)
        except Error as error:
            raise Exception(error)

    def clear_storage(self):
        cursor = self.connection.cursor()

        cursor.execute(self.delete_all_task_data_query)
        cursor.execute(self.delete_all_flow_data_query)

        cursor.close()
        self.connection.commit()

    """
    FLOWS
    """
    def get_max_flow_execution_id(self) -> int:
        cursor = self.connection.cursor()
        cursor.execute(self.select_current_execution_id_query)

        rows = cursor.fetchall()
        if(len(rows) != 1):
            raise ValueError("Select current execution id query should only return one result!")

        return 1 if rows[0][0] is None else rows[0][0] + 1

    def save_flow(self, flow_execution: FlowExecution) -> FlowExecution:
        flow_dao = FlowMapper.to_dao(flow_execution)

        cursor = self.connection.cursor()
        cursor.execute(self.insert_flow_query, flow_dao)

        rows = cursor.fetchall()
        if(len(rows) != 1):
            raise ValueError("Insert flow query should only return one result!")

        cursor.close()
       
        self.connection.commit()

        return FlowMapper.to_model(rows[0])
        
    def get_flow(self, execution_id: int) -> FlowExecution:
        cursor = self.connection.cursor()

        query_param = (execution_id,)
        cursor.execute(self.select_get_flow_query, query_param)
        rows = cursor.fetchall()

        if(len(rows) == 0):
            return None

        if(len(rows) > 1):
            raise ValueError("Select get flow query should only return one result!")
        
        return FlowMapper.to_model(rows[0])
    
    def get_run_candidate_flow(self, strategy: FlowStatus) -> FlowExecution:
        cursor = self.connection.cursor()

        query_param = (strategy.name,)
        cursor.execute(self.select_get_candidate_flow_id, query_param)
        rows = cursor.fetchall()

        if(len(rows) == 0):
            return None
        
        if(len(rows) > 1):
            raise ValueError("Select get run candidate flow query should return only one result!")
        
        return FlowMapper.to_model(rows[0])

    """
    TASKS
    """
    def save_task(self, task: TaskExecution) -> TaskExecution:
        task_dao = TaskMapper.to_dao(task)

        cursor = self.connection.cursor()
        cursor.execute(self.insert_task_query, task_dao)

        rows = cursor.fetchall()
        if(len(rows) != 1):
            raise ValueError("Insert task query should only return one result!")

        cursor.close()
       
        self.connection.commit()

        return TaskMapper.to_model(rows[0])
    
    def get_flow_task_execution_history(self, flow_id: int) -> list[TaskExecution]:
        cursor = self.connection.cursor()

        query_param = (flow_id,)
        cursor.execute(self.select_flow_task_execution_history_query, query_param)
        rows = cursor.fetchall()

        ret_val = []
        for row in rows:
            ret_val.append(TaskMapper.to_model(row))

        return ret_val

class FlowMapper:
    @staticmethod
    def to_dao(model: FlowExecution) -> tuple[int,int,str,str,int,str]:
        execution_context_json = model.execution_context.to_json()
        return (model.execution_id, model.execution_step, model.status.name, model.template_name, model.current_task_index, execution_context_json, model.timestamp)

    @staticmethod
    def to_model(dao: tuple[int,int,str,str,int,str,int]) -> FlowExecution:
        fe = FlowExecution()
        fe.execution_id = dao[0]
        fe.execution_step = dao[1]
        fe.status = FlowStatus[dao[2]]
        fe.template_name = dao[3]
        fe.current_task_index = dao[4]
        fe.execution_context = ExecutionContext.from_json(dao[5])
        fe.timestamp = dao[6]

        return fe

class TaskMapper:
    @staticmethod
    def to_dao(model:TaskExecution) -> tuple[int,int,str,str]:
        return (model.flow_execution_id, model.flow_execution_step, model.status.name, model.output, model.timestamp)

    @staticmethod
    def to_model(dao: tuple[int,int,str,str,int]) -> TaskExecution:

        te = TaskExecution()
        te.flow_execution_id = dao[0]
        te.flow_execution_step = dao[1]
        te.status = TaskStatus[dao[2]]
        te.output = dao[3]
        te.timestamp = dao[4]

        return te