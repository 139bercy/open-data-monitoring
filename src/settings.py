import os

from dotenv import load_dotenv

from application.services.dataset import DatasetMonitoring
from application.services.platform import PlatformMonitoring
from infrastructure.adapters.in_memory import (
    InMemoryDatasetRepository,
    InMemoryPlatformRepository,
)
from infrastructure.adapters.postgres import (
    PostgresDatasetRepository,
    PostgresPlatformRepository,
)
from infrastructure.database.postgres import PostgresClient
from infrastructure.factories.dataset import DatasetAdapterFactory

load_dotenv(".env")

BASE_DIR = "db"
ENV = os.environ["OPEN_DATA_MONITORING_ENV"]


class App:
    def __init__(self, platform, dataset):
        self.platform = platform
        self.dataset = dataset


client = PostgresClient(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host="localhost",
        port=5432,
)


if ENV == "PROD":  # pragma: no cover
    raise NotImplementedError
elif ENV == "TEST":
    print(f"App environment = {ENV}")
    platform = PlatformMonitoring(
        repository=InMemoryPlatformRepository([]),
    )
    dataset = DatasetMonitoring(repository=InMemoryDatasetRepository([]))
    app = App(platform=platform, dataset=dataset)
else:  # pragma: no cover
    print(f"App environment = {ENV}")
    platform = PlatformMonitoring(
        repository=PostgresPlatformRepository(client=client),
    )
    dataset = DatasetMonitoring(repository=PostgresDatasetRepository(client=client))
    app = App(platform=platform, dataset=dataset)
