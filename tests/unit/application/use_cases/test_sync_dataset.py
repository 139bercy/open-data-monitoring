from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from application.use_cases.sync_dataset import SyncDatasetCommand, SyncDatasetUseCase


@pytest.fixture
def sync_dependencies():
    with (
        patch("application.use_cases.sync_dataset.DatasetAdapterFactory") as af,
        patch("domain.datasets.factory.DatasetFactory.create_from_adapter") as df,
    ):
        repo, uow = MagicMock(), MagicMock()
        adapter = af.return_value.create.return_value
        yield repo, uow, adapter, df


@pytest.fixture
def use_case(sync_dependencies):
    repo, uow, _, _ = sync_dependencies
    return SyncDatasetUseCase(repository=repo, uow=uow)


def test_sync_success(use_case, sync_dependencies, ods_platform, ods_dataset):
    # Arrange
    repo, _, adapter, df = sync_dependencies
    adapter.fetch.return_value = ods_dataset
    df.return_value = MagicMock(id=uuid4(), buid="b", slug="s", raw=ods_dataset, checksum="h")
    # Act
    result = use_case.handle(SyncDatasetCommand(ods_platform, "id"))
    # Assert
    assert result.status == "success"
    repo.add.assert_called_once()


def test_sync_failure(use_case, sync_dependencies, ods_platform):
    # Arrange
    repo, _, adapter, _ = sync_dependencies
    adapter.fetch.return_value = {"sync_status": "failed"}
    # Act
    result = use_case.handle(SyncDatasetCommand(ods_platform, "id"))
    # Assert
    assert result.status == "failed"
    repo.add.assert_not_called()
