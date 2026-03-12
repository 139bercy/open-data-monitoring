from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4

from domain.platform.aggregate import Platform
from domain.platform.ports import PlatformRepository


@dataclass(frozen=True)
class CreatePlatformCommand:
    name: str
    slug: str
    organization_id: str
    type: str
    url: str
    key: Optional[str] = None


@dataclass(frozen=True)
class CreatePlatformOutput:
    platform_id: UUID
    status: str


class CreatePlatformUseCase:
    def __init__(self, uow):
        self.uow = uow

    @property
    def repository(self) -> PlatformRepository:
        return self.uow.platforms

    def handle(self, command: CreatePlatformCommand) -> CreatePlatformOutput:
        """
        Registers a new open data platform.
        """
        instance = self._create_instance(command)
        return self._persist(instance)

    def _create_instance(self, command: CreatePlatformCommand) -> Platform:
        return Platform(
            id=uuid4(),
            name=command.name,
            slug=command.slug,
            organization_id=command.organization_id,
            type=command.type,
            url=command.url,
            key=command.key,
        )

    def _persist(self, instance: Platform) -> CreatePlatformOutput:
        with self.uow:
            self.repository.save(instance)
            return CreatePlatformOutput(platform_id=instance.id, status="success")
