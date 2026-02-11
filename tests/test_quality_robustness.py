from __future__ import annotations

import uuid
from datetime import datetime

from application.services.quality_assessment import QualityAssessmentService
from domain.common.value_objects import Slug
from domain.datasets.aggregate import Dataset
from infrastructure.llm.openai_evaluator import OpenAIEvaluator
from infrastructure.unit_of_work import InMemoryUnitOfWork


class MockEvaluator(OpenAIEvaluator):
    def __init__(self):
        pass

    def evaluate_metadata(self, dataset, dcat_reference, charter, output):
        from domain.quality.evaluation import MetadataEvaluation

        return MetadataEvaluation(
            dataset_id=None,
            dataset_slug="test",
            evaluated_at=datetime.now(),
            overall_score=0.0,
            criteria_scores={},
            suggestions=[],
        )


def test_quality_assessment_reconstruction_and_null_safe():
    """Verify that quality assessment uses the merged snapshot and handles null metadata."""
    uow = InMemoryUnitOfWork()
    evaluator = MockEvaluator()
    service = QualityAssessmentService(evaluator=evaluator, uow=uow)

    dataset_id = uuid.uuid4()
    # Dataset with null fields that previously caused AttributeErrors/KeyErrors
    dataset = Dataset(
        id=dataset_id,
        platform_id=uuid.uuid4(),
        buid="test-buid",
        slug=Slug("test-slug"),
        title="Test Dataset",
        page="http://test.com",
        created=datetime.now(),
        modified=datetime.now(),
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={"metas": {"default": {"description": None, "publisher": "Test Publisher"}}},
    )

    with uow:
        uow.datasets.add(dataset)
        uow.commit()

    # Should not raise AttributeError or KeyError
    service.evaluate_dataset(dataset_id, "docs/quality/dcat_reference.md", "docs/quality/charter_opendata.md", "json")

    # Verify has_description is False but handled
    updated_ds = uow.datasets.get(dataset_id)
    assert updated_ds.quality.has_description is False
