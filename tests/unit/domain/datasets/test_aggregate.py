from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from domain.common.enums import SyncStatus
from domain.datasets.aggregate import Dataset


@pytest.fixture
def base_dataset_data():
    return {
        "id": uuid4(),
        "platform_id": uuid4(),
        "buid": "test-buid",
        "slug": "test-dataset",
        "title": "Test Dataset",
        "page": "http://example.com/dataset",
        "created": datetime.now(timezone.utc) - timedelta(days=100),
        "modified": datetime.now(timezone.utc),
        "published": True,
        "restricted": False,
        "raw": {},
        "downloads_count": 0,
        "api_calls_count": 0,
        "views_count": 0,
        "reuses_count": 0,
        "followers_count": 0,
        "popularity_score": 0.0,
        "last_sync_status": SyncStatus.SUCCESS,
        "is_deleted": False,
    }


def test_calculate_discoverability_kpi_freshness_daily(base_dataset_data):
    """
    Intention: Verify that a dataset with a 'daily' frequency gets a freshness score of 100
    if updated 1 day ago, 50 if updated 3 days ago, and 0 if updated 5 days ago.
    """
    # 1 day ago (<= 2 days) -> 100
    data = base_dataset_data.copy()
    data["raw"] = {"frequency": "daily"}
    data["modified"] = datetime.now(timezone.utc) - timedelta(days=1)
    dataset = Dataset(**data)

    kpi1 = dataset.calculate_discoverability_kpi()
    assert kpi1.freshness_score == 100.0

    # 3 days ago (<= 4 days) -> 50
    data["modified"] = datetime.now(timezone.utc) - timedelta(days=3)
    dataset2 = Dataset(**data)
    kpi2 = dataset2.calculate_discoverability_kpi()
    assert kpi2.freshness_score == 50.0

    # 5 days ago (> 4 days) -> 0
    data["modified"] = datetime.now(timezone.utc) - timedelta(days=5)
    dataset3 = Dataset(**data)
    kpi3 = dataset3.calculate_discoverability_kpi()
    assert kpi3.freshness_score == 0.0


def test_calculate_discoverability_kpi_freshness_unknown(base_dataset_data):
    """
    Intention: Verify that a dataset with no frequency gets the default 90 days penalty threshold.
    """
    data = base_dataset_data.copy()
    data["raw"] = {}  # No frequency

    # 89 days ago -> 100
    data["modified"] = datetime.now(timezone.utc) - timedelta(days=89)
    dataset1 = Dataset(**data)
    assert dataset1.calculate_discoverability_kpi().freshness_score == 100.0

    # 150 days ago -> 50
    data["modified"] = datetime.now(timezone.utc) - timedelta(days=150)
    dataset2 = Dataset(**data)
    assert dataset2.calculate_discoverability_kpi().freshness_score == 50.0


def test_calculate_impact_kpi_engagement(base_dataset_data):
    """
    Intention: Verify that Impact KPI correctly calculates engagement rate and usage intensity
    from the raw metrics.
    """
    data = base_dataset_data.copy()
    data["views_count"] = 100
    data["reuses_count"] = 5
    data["api_calls_count"] = 50
    data["downloads_count"] = 150

    dataset = Dataset(**data)
    kpi = dataset.calculate_impact_kpi()

    assert kpi.engagement_rate == 5 / 100  # 0.05
    assert kpi.usage_intensity == 50 / 200  # 0.25


def test_calculate_discoverability_kpi_handles_null_metas(base_dataset_data):
    """
    Intention: Verify that `calculate_discoverability_kpi` does NOT raise an AttributeError
    if `raw.metas` is explicitly set to None (null in JSON).
    """
    data = base_dataset_data.copy()
    data["raw"] = {"metas": None}  # This simulates an explicitly missing/null metas object
    dataset = Dataset(**data)

    # This should not raise an exception
    kpi = dataset.calculate_discoverability_kpi()
    # If the bug is not triggered, freshness should default to the 90-day threshold logic
    assert kpi.freshness_score in [0.0, 50.0, 100.0]
