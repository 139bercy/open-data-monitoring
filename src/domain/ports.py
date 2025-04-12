from asyncio import Protocol


class PlatformAdapter(Protocol):
    def fetch_datasets(self) -> dict:       # pragma: no cover
        """Retourne le nombre de datasets disponibles sur la plateforme"""
        raise NotImplementedError
