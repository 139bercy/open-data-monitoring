from datetime import datetime
from uuid import uuid4

import pytest

from domain.common.value_objects import InvalidDomainValue, Slug, Url
from domain.datasets.aggregate import Dataset


def test_slug_validation():
    # Valid slugs
    assert str(Slug("valid-slug")) == "valid-slug"
    assert str(Slug("slug123")) == "slug123"

    # Invalid slugs
    with pytest.raises(InvalidDomainValue):
        Slug("Invalid Slug")
    with pytest.raises(InvalidDomainValue):
        Slug("slug!")
    with pytest.raises(InvalidDomainValue):
        Slug("")


def test_url_validation():
    # Valid URLs
    assert str(Url("https://example.com")) == "https://example.com"
    assert str(Url("http://localhost:8080/path")) == "http://localhost:8080/path"

    # Invalid URLs
    with pytest.raises(InvalidDomainValue):
        Url("not-a-url")
    with pytest.raises(InvalidDomainValue):
        Url("ftp://invalid")
    with pytest.raises(InvalidDomainValue):
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
