from infrastructure.adapters import (
    OpendatasoftAdapter,
    DataGouvFrAdapter,
    InMemoryAdapter,
)


class AdapterFactory:
    @staticmethod
    def create(platform_type: str, url: str, key: str, name: str):
        if platform_type == "opendatasoft":
            return OpendatasoftAdapter(url, key, name)
        elif platform_type == "datagouvfr":
            return DataGouvFrAdapter(url, key, name)
        elif platform_type == "test":
            return InMemoryAdapter(url, key, name)
        else:
            raise ValueError("Unsupported platform type")
