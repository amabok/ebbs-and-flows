CREATE TABLE IF NOT EXISTS flow_executions(
        execution_id integer NOT NULL,
        execution_step integer NOT NULL,
        status text, 
        template_name text,
        current_task_index integer,
        execution_context text, 
        timestamp integer, 
        PRIMARY KEY(execution_id, execution_step)
        );

CREATE TABLE IF NOT EXISTS task_executions(
        flow_execution_id integer,
        flow_execution_step integer,
        status text,output text,
        timestamp integer,
        FOREIGN KEY (flow_execution_id, flow_execution_step) REFERENCES flow_executions(execution_id, execution_step)
        );