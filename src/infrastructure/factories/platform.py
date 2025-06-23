from domain.platform.ports import (AbstractPlatformAdapterFactory,
                                   PlatformAdapter)
from infrastructure.adapters.datagouvfr import DataGouvFrAdapter
from infrastructure.adapters.in_memory import InMemoryAdapter
from infrastructure.adapters.ods import OpendatasoftAdapter


class PlatformAdapterFactory(AbstractPlatformAdapterFactory):
    def create(
        self, platform_type: str, url: str, key: str, slug: str
    ) -> PlatformAdapter:
        if platform_type == "opendatasoft":
            return OpendatasoftAdapter(url=url, key=key, slug=slug)
        elif platform_type == "datagouvfr":
            return DataGouvFrAdapter(url=url, key=key, slug=slug)
        elif platform_type == "test":
            return InMemoryAdapter(url=url, key=key, slug=slug)
        else:
            raise ValueError("Unsupported platform type")
