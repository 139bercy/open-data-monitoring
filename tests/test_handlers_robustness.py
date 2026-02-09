from unittest.mock import MagicMock

import pytest

from application.handlers import fetch_dataset, find_dataset_id_from_url, find_platform_from_url, get_publishers_stats
from domain.datasets.exceptions import DatasetUnreachableError


def test_find_platform_from_url_value_error(app):
    # Mock repository to raise ValueError when get_by_domain is called
    app.platform.repository.get_by_domain = MagicMock(side_effect=ValueError("Invalid domain"))

    result = find_platform_from_url(app=app, url="https://invalid-url.com")
    assert result is None


def test_find_dataset_id_from_url_platform_not_found(app):
    # Ensure find_platform_from_url returns None
    app.platform.repository.get_by_domain = MagicMock(side_effect=ValueError())

    result = find_dataset_id_from_url(app=app, url="https://unknown.com")
    assert result is None


def test_fetch_dataset_unreachable_error(app, ods_platform):
    # Mock adapter fetch to raise DatasetUnreachableError

    mock_adapter = MagicMock()
    mock_adapter.fetch = MagicMock(side_effect=DatasetUnreachableError())

    # We need to mock the factory to return our mock adapter
    with pytest.MonkeyPatch().context() as m:
        m.setattr(
            "infrastructure.factories.dataset.DatasetAdapterFactory.create", lambda self, platform_type: mock_adapter
        )

        result = fetch_dataset(platform=ods_platform, dataset_id="ghost")

        assert result["sync_status"] == "failed"
        assert result["slug"] == "ghost"


def test_get_publishers_stats_coverage(app):
    # Just ensure it calls the repository
    app.dataset.repository.get_publishers_stats = MagicMock(return_value=[{"publisher": "Test", "dataset_count": 1}])

    result = get_publishers_stats(app)
    assert len(result) == 1
    assert result[0]["publisher"] == "Test"
