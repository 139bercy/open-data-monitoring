import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime
from dataclasses import dataclass
from application.services.quality_assessment import QualityAssessmentService

@dataclass
class MockEval:
    dataset_id: any = None
    dataset_slug: str = ""
    overall_score: float = 80.0
    evaluated_at: datetime = datetime.now()

@pytest.fixture
def qa_deps():
    uow, evaluator = MagicMock(), MagicMock()
    dataset = MagicMock(id=uuid4(), slug=MagicMock(), versions=[], downloads_count=0, api_calls_count=0)
    dataset.slug.is_valid.return_value = True
    uow.datasets.get.return_value = dataset
    return uow, evaluator, dataset

@pytest.fixture
def service(qa_deps):
    uow, evaluator, _ = qa_deps
    return QualityAssessmentService(evaluator=evaluator, uow=uow)

def test_evaluate_dataset_success(service, qa_deps):
    # Arrange
    uow, evaluator, dataset = qa_deps
    evaluator.evaluate_metadata.return_value = MockEval()
    with patch.object(service, "_load_markdown", return_value="# Doc"):
        # Act
        res = service.evaluate_dataset(dataset.id, "d", "c", "json")
    # Assert
    assert res.overall_score == 80.0
    uow.commit.assert_called_once()

def test_evaluate_dataset_not_found(service, qa_deps):
    # Arrange
    uow, _, _ = qa_deps
    uow.datasets.get.return_value = None
    # Act & Assert
    with pytest.raises(ValueError, match="Dataset not found"):
        service.evaluate_dataset(uuid4(), "d", "c", "json")
