from uuid import uuid4

import pytest

from domain.platform.aggregate import Platform
from infrastructure.unit_of_work import PostgresUnitOfWork
from tests.fixtures.fixtures import platform_1


@pytest.mark.usefixtures("setup_test_database")
def test_unit_of_work_commit(db_transaction, platform):
    # Arrange
    uow = PostgresUnitOfWork(client=db_transaction)
    # Act
    with uow:
        uow.platforms.save(platform)
        uow.commit()
    # Assert
    with uow:
        saved_platform = uow.platforms.get(platform.id)
        assert saved_platform is not None
        assert saved_platform.name == platform.name


def test_unit_of_work_rollback(db_transaction, platform):
    # Arrange
    uow = PostgresUnitOfWork(client=db_transaction)
    # Act & Assert
    with uow:
        uow.platforms.save(platform)
        uow.rollback()
    with uow:
        saved_platform = uow.platforms.get(platform.id)
        assert saved_platform is None


def test_unit_of_work_context_manager_commit(db_transaction, platform):
    # Arrange
    uow = PostgresUnitOfWork(client=db_transaction)
    # Act
    with uow:
        uow.platforms.save(platform)
    # Assert
    with uow:
        saved_platform = uow.platforms.get(platform.id)
        assert saved_platform is not None
        assert saved_platform.name == platform.name


def test_unit_of_work_context_manager_rollback_on_exception(db_transaction, platform):
    # Arrange
    uow = PostgresUnitOfWork(client=db_transaction)
    # Act & Assert
    with pytest.raises(Exception):
        with uow:
            uow.platforms.save(platform)
            raise Exception("Test exception")
    with uow:
        saved_platform = uow.platforms.get(platform.id)
        assert saved_platform is None
