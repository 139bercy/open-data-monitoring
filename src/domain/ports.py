from asyncio import Protocol


class PlatformAdapter(Protocol):
    def fetch_datasets(self) -> int:
        """Retourne le nombre de datasets disponibles sur la plateforme"""
        raise NotImplementedError
