from datetime import datetime, timezone
from uuid import uuid4

from domain.datasets.aggregate import Dataset


def test_dataset_size_metrics_initialization():
    """Verify that records_count and size_bytes are correctly initialized."""
    dataset_id = uuid4()
    platform_id = uuid4()

    dataset = Dataset(
        id=dataset_id,
        platform_id=platform_id,
        buid="test-buid",
        slug="test-slug",
        title="Test Title",
        page="http://example.com",
        created=datetime.now(timezone.utc),
        modified=datetime.now(timezone.utc),
        published=True,
        restricted=False,
        downloads_count=10,
        api_calls_count=20,
        raw={},
        records_count=1000,
        size_bytes=1048576,  # 1 MB
    )

    assert dataset.records_count == 1000
    assert dataset.size_bytes == 1048576


def test_dataset_from_dict_with_size_metrics():
    """Verify that from_dict correctly handles records_count and size_bytes."""
    data = {
        "id": str(uuid4()),
        "platform_id": str(uuid4()),
        "buid": "test-buid",
        "slug": "test-slug",
        "title": "Test Title",
        "page": "http://example.com",
        "created": datetime.now(timezone.utc).isoformat(),
        "modified": datetime.now(timezone.utc).isoformat(),
        "published": True,
        "restricted": False,
        "raw": {},
        "records_count": 500,
        "size_bytes": 1024,
    }

    dataset = Dataset.from_dict(data)

    assert dataset.records_count == 500
    assert dataset.size_bytes == 1024


def test_dataset_to_dict_includes_size_metrics():
    """Verify that to_dict includes records_count and size_bytes."""
    dataset = Dataset(
        id=uuid4(),
        platform_id=uuid4(),
        buid="test-buid",
        slug="test-slug",
        title="Test Title",
        page="http://example.com",
        created=datetime.now(timezone.utc),
        modified=datetime.now(timezone.utc),
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={},
        records_count=777,
        size_bytes=999,
    )

    result = dataset.to_dict()

    assert result["records_count"] == 777
    assert result["size_bytes"] == 999
