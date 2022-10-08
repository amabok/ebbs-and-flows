from src.model.flow import ExecutionContext, FlowExecution, FlowStatus, PersistenceMode
from src.repositories.flow_repository import FlowRepository
import pytest

class TestPersistentFlowRepository:
    subject = None

    @pytest.fixture(autouse=True)
    def before_tests(self):
        self.subject: FlowRepository = FlowRepository.from_persistence_mode(PersistenceMode.PERSISTENT)
        #TODO: remove from here after fixing the clearing problem between each test
        self.subject.clear_storage()

    #TODO: how to make sure this runs after each test
    #@pytest.fixture(autouse=True)
    #def after_tests(self):
    #    self.subject.clear_all_data()

    def test_persistent_repository_usage(self):
        # Given
        flow = FlowExecution()
        flow.template_name = "name"
        flow.status = FlowStatus.RUNNING
        flow.execution_id = 123
        flow.execution_step = 12
        flow.current_task_index = 4
        flow.timestamp = 5

        ec = ExecutionContext()
        ec.set("some_field", "some value") 
        ec.set("another_field", 42)
        flow.execution_context = ec

        try:
            # When
            saved_flow = self.subject.save_flow(flow)
            self.subject.refresh()
            
            # Then
            retrieved_flow = self.subject.get_flow(saved_flow.execution_id)

            assert(saved_flow.template_name == retrieved_flow.template_name)
            assert(saved_flow.status == retrieved_flow.status)        
            assert(saved_flow.execution_id == retrieved_flow.execution_id)
            assert(saved_flow.execution_step == retrieved_flow.execution_step)
            assert(saved_flow.current_task_index == retrieved_flow.current_task_index)
            assert(saved_flow.timestamp == retrieved_flow.timestamp)

            assert(saved_flow.execution_context.get("some_field") == retrieved_flow.execution_context.get("some_field"))
            assert(saved_flow.execution_context.get("another_field") == retrieved_flow.execution_context.get("another_field"))

        #TODO: find a more elegant way of cleaning up the data after each test 
        finally:
            self.subject.clear_storage()