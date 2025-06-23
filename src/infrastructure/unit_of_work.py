from domain.unit_of_work import UnitOfWork
from infrastructure.adapters.postgres import (
    PostgresDatasetRepository,
    PostgresPlatformRepository,
)
from infrastructure.database.postgres import PostgresClient


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
    def platforms(self) -> PostgresPlatformRepository:
        if self._platforms is None:
            self._platforms = PostgresPlatformRepository(self.client)
        return self._platforms

    @property
    def datasets(self) -> PostgresDatasetRepository:
        if self._datasets is None:
            self._datasets = PostgresDatasetRepository(self.client)
        return self._datasets
