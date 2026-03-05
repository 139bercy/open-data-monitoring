from abc import ABC, abstractmethod

from domain.auth.ports import UserRepository
from domain.datasets.ports import AbstractDatasetRepository
from domain.platform.ports import PlatformRepository


class UnitOfWork(ABC):  # pragma: no cover
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def platforms(self) -> PlatformRepository:
        raise NotImplementedError

    @property
    @abstractmethod
    def datasets(self) -> AbstractDatasetRepository:
        raise NotImplementedError

    @property
    @abstractmethod
    def users(self) -> UserRepository:
        raise NotImplementedError
