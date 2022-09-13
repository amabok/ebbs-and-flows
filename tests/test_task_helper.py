from re import sub
from typing import ByteString
from model.flow import ExecutionContext, TaskStatus
from tests.task_helper import FailingTask, RoundRobinTask, SuccessfulTask
import pytest

class TestTaskHelper:    
    def test_sucessful_task(self):
        # Given
        subject = SuccessfulTask()
        
        # When
        result = subject.run(ExecutionContext())

        # Then
        assert(result.get("some_output")=="OK")

    def test_failing_task(self):
        # Given
        subject = FailingTask()
        
        # When / Then
        with pytest.raises(ValueError) as exc:
            subject.run(ExecutionContext())

        raised_expection = exc.value
        assert(type(raised_expection) is ValueError)

    def test_round_robin_failing_task(self):
       # Given
       subject = RoundRobinTask(TaskStatus.SUCCEEDED)

       # When / Then

       # First run
       ec = subject.run(ExecutionContext()) 
       assert(ec.get("some_output") == "OK")

       # Second run
       with pytest.raises(ValueError) as exc:
        subject.run(ec)
       raised_expection = exc.value
       assert(type(raised_expection) is ValueError)

       # Third run
       ec = subject.run(ExecutionContext()) 
       assert(ec.get("some_output") == "OK")