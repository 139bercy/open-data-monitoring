from domain.platform.ports import AbstractPlatformAdapterFactory, PlatformAdapter
from infrastructure.adapters.platforms.datagouvfr import DataGouvPlatformAdapter
from infrastructure.adapters.platforms.in_memory import InMemoryAdapter
from infrastructure.adapters.platforms.ods import OpendatasoftPlatformAdapter


class PlatformAdapterFactory(AbstractPlatformAdapterFactory):
    def create(self, platform_type: str, url: str, key: str, slug: str) -> PlatformAdapter:
        if platform_type == "opendatasoft":
            return OpendatasoftPlatformAdapter(url=url, key=key, slug=slug)
        elif platform_type == "datagouv":
            return DataGouvPlatformAdapter(url=url, key=key, slug=slug)
        elif platform_type == "test":
            return InMemoryAdapter(url=url, key=key, slug=slug)
        else:
            raise ValueError("Unsupported platform type")
