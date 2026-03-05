from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from application.use_cases.sync_platform import SyncPlatformCommand, SyncPlatformUseCase


@pytest.fixture
def sync_p_deps():
    with patch("application.use_cases.sync_platform.PlatformAdapterFactory") as af:
        repo, uow = MagicMock(), MagicMock()
        adapter = af.return_value.create.return_value
        yield repo, uow, adapter


@pytest.fixture
def use_case(sync_p_deps):
    repo, uow, _ = sync_p_deps
    return SyncPlatformUseCase(repository=repo, uow=uow)


def test_sync_platform_success(use_case, sync_p_deps):
    # Arrange
    repo, _, adapter = sync_p_deps
    repo.get.return_value = MagicMock(type="t", url="https://v.com", key="k", slug="s")
    adapter.fetch.return_value = {"timestamp": "t", "status": "s", "datasets_count": 1}
    # Act
    result = use_case.handle(SyncPlatformCommand(uuid4()))
    # Assert
    assert result.status == "success"
    repo.save_sync.assert_called_once()


def test_sync_platform_not_found(use_case, sync_p_deps):
    # Arrange
    repo, _, _ = sync_p_deps
    repo.get.return_value = None
    # Act
    result = use_case.handle(SyncPlatformCommand(uuid4()))
    # Assert
    assert result.status == "failed"
    assert result.message == "Not found"
