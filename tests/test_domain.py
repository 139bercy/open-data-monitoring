from datetime import datetime
from uuid import uuid4

import pytest

from domain.common.value_objects import InvalidDomainValueError, Slug, Url
from domain.datasets.aggregate import Dataset


def test_slug_validation():
    # Valid slugs
    assert str(Slug("valid-slug")) == "valid-slug"
    assert str(Slug("slug123")) == "slug123"

    # Invalid slugs
    with pytest.raises(InvalidDomainValueError):
        Slug("Invalid Slug")
    with pytest.raises(InvalidDomainValueError):
        Slug("slug!")
    with pytest.raises(InvalidDomainValueError):
        Slug("")


def test_url_validation():
    # Valid URLs
    assert str(Url("https://example.com")) == "https://example.com"
    assert str(Url("http://localhost:8080/path")) == "http://localhost:8080/path"

    # Invalid URLs
    with pytest.raises(InvalidDomainValueError):
        Url("not-a-url")
    with pytest.raises(InvalidDomainValueError):
        Url("ftp://invalid")
    with pytest.raises(InvalidDomainValueError):
        Url("")


def test_dataset_stable_hashing():
    dataset_id = uuid4()
    platform_id = uuid4()
    now = datetime.now()

    dataset = Dataset(
        id=dataset_id,
        platform_id=platform_id,
        buid="buid1",
        slug="my-dataset",
        title="My Dataset",
        page="https://data.com/d1",
        created=now,
        modified=now,
        published=True,
        restricted=False,
        downloads_count=10,
        api_calls_count=20,
        raw={"something": "irrelevant"},  # Raw data NO LONGER affects the hash
    )

    hash1 = dataset.calculate_hash()

    # Change raw data
    dataset.raw["something"] = "different"
    hash2 = dataset.calculate_hash()

    assert hash1 == hash2  # Hash should be stable despite raw data change

    # Change domain field
    dataset.slug = Slug("my-dataset-new")
    hash3 = dataset.calculate_hash()

    assert hash1 != hash3  # Hash should change when domain field changes


def test_dataset_deletion_state_transitions():
    now = datetime.now()
    dataset = Dataset(
        id=uuid4(),
        platform_id=uuid4(),
        buid="buid1",
        slug="slug",
        title="Title",
        page="https://data.com",
        created=now,
        modified=now,
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={},
    )

    # State: Active -> Deleted
    dataset.mark_as_deleted()
    assert dataset.is_deleted is True

    # State: Deleted -> Error (Already Deleted)
    from domain.datasets.exceptions import DatasetAlreadyDeletedError

    with pytest.raises(DatasetAlreadyDeletedError):
        dataset.mark_as_deleted()

    # State: Deleted -> Active
    dataset.restore()
    assert dataset.is_deleted is False

    # State: Active -> Error (Not Deleted)
    from domain.datasets.exceptions import DatasetNotDeletedError

    with pytest.raises(DatasetNotDeletedError):
        dataset.restore()


def test_dataset_metrics_validation():
    now = datetime.now()
    dataset = Dataset(
        id=uuid4(),
        platform_id=uuid4(),
        buid="buid1",
        slug="slug",
        title="Title",
        page="https://data.com",
        created=now,
        modified=now,
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={},
    )

    # Valid update
    dataset.update_metrics(downloads=100, api_calls=50)
    assert dataset.downloads_count == 100
    assert dataset.api_calls_count == 50

    # Invalid update (negative value)
    from domain.datasets.exceptions import InvalidMetricValueError

    with pytest.raises(InvalidMetricValueError) as exc:
        dataset.update_metrics(views=-1)
    assert "views_count" in str(exc.value)
    assert "-1" in str(exc.value)


def test_dataset_cooldown_calculation():
    from datetime import timedelta, timezone

    from domain.common.constants import DEFAULT_VERSIONING_COOLDOWN_HOURS

    now = datetime.now(timezone.utc)
    dataset = Dataset(
        id=uuid4(),
        platform_id=uuid4(),
        buid="buid1",
        slug="slug",
        title="Title",
        page="https://data.com",
        created=now,
        modified=now,
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={},
        last_version_timestamp=now - timedelta(hours=DEFAULT_VERSIONING_COOLDOWN_HOURS - 0.1),  # 14.9h if 15h
    )

    # Cooldown should be active
    assert dataset.is_cooldown_active() is True

    # Move timestamp back to more than cooldown
    dataset.last_version_timestamp = now - timedelta(hours=DEFAULT_VERSIONING_COOLDOWN_HOURS + 0.1)
    assert dataset.is_cooldown_active() is False
