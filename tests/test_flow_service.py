from logging import exception
from src.model.flow import ExecutionContext, FlowStatus, PersistenceMode
from src.services.flow_service import FlowService
import pytest

class TestFlowService:
    subject = None

    @pytest.fixture(autouse=True)
    def before_tests(self):
        self.subject = FlowService(PersistenceMode.TRANSIENT)
    
    def test_get_non_existent_flow(self):
        # Given
        non_existent_flow_id = 666

        flow = self.subject.create_flow_execution("template", ExecutionContext())

        # When/Then
        with pytest.raises(ValueError) as exc:
            self.subject.get_flow_execution(non_existent_flow_id)

        raised_expection = exc.value
        assert(type(raised_expection) is ValueError)

    def test_update_flow_with_not_allowed_target_status(self):
        # Given
        execution_context = ExecutionContext()
        flow = self.subject.create_flow_execution("template", execution_context)

        # When/Then
        with pytest.raises(ValueError) as exc:
            self.subject.update_flow_status(flow.execution_id, FlowStatus.FAILED, execution_context)

        raised_expection = exc.value
        assert(type(raised_expection) is ValueError)