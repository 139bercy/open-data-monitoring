from domain.datasets.ports import AbstractDatasetRepository
from domain.platform.ports import PlatformRepository
from domain.unit_of_work import UnitOfWork
from infrastructure.database.postgres import PostgresClient
from infrastructure.repositories.datasets.in_memory import InMemoryDatasetRepository
from infrastructure.repositories.datasets.postgres import PostgresDatasetRepository
from infrastructure.repositories.platforms.in_memory import InMemoryPlatformRepository
from infrastructure.repositories.platforms.postgres import PostgresPlatformRepository


class PostgresUnitOfWork(UnitOfWork):
    def __init__(self, client: PostgresClient):
        self.client = client
        self._platforms = None
        self._datasets = None
        self._in_transaction = False

    def __enter__(self):
        self._in_transaction = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()
        finally:
            self._in_transaction = False

    def commit(self):
        if self._in_transaction:
            self.client.commit()

    def rollback(self):
        if self._in_transaction:
            self.client.rollback()
            # Réinitialiser les repositories après un rollback
            self._platforms = None
            self._datasets = None

    @property
    def platforms(self) -> PlatformRepository:
        if self._platforms is None:
            self._platforms = PostgresPlatformRepository(self.client)
        return self._platforms

    @property
    def datasets(self) -> AbstractDatasetRepository:
        if self._datasets is None:
            self._datasets = PostgresDatasetRepository(self.client)
        return self._datasets


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self):
        self._platforms = InMemoryPlatformRepository([])
        self._datasets = InMemoryDatasetRepository([])
        self._in_transaction = False
        self._pending_changes = []

    def __enter__(self):
        self._in_transaction = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._in_transaction = False
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    def commit(self):
        if self._in_transaction:
            self._pending_changes = []

    def rollback(self):
        if self._in_transaction:
            self._pending_changes = []

    @property
    def platforms(self) -> PlatformRepository:
        return self._platforms

    @property
    def datasets(self) -> AbstractDatasetRepository:
        return self._datasets
