import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from dataclasses import dataclass
from application.use_cases.evaluate_dataset import EvaluateDatasetUseCase, EvaluateDatasetCommand

@dataclass
class MockEvalResult:
    score: int = 100
    overall_score: float = 100.0

@pytest.fixture
def eval_deps():
    with patch("application.use_cases.evaluate_dataset.QualityAssessmentService") as qas:
        uow = MagicMock()
        evaluator = MagicMock()
        service = qas.return_value
        yield uow, evaluator, service

@pytest.fixture
def use_case(eval_deps):
    uow, evaluator, _ = eval_deps
    return EvaluateDatasetUseCase(uow=uow, evaluator=evaluator)

def test_evaluate_success(use_case, eval_deps):
    # Arrange
    _, _, service = eval_deps
    service.evaluate_dataset.return_value = MockEvalResult()
    # Act
    result = use_case.handle(EvaluateDatasetCommand(uuid4()))
    # Assert
    assert result.status == "success"
    assert result.evaluation["score"] == 100

def test_evaluate_failure(use_case, eval_deps):
    # Arrange
    _, _, service = eval_deps
    service.evaluate_dataset.side_effect = Exception("error")
    # Act
    result = use_case.handle(EvaluateDatasetCommand(uuid4()))
    # Assert
    assert result.status =="failed"
    assert "error" in result.error
