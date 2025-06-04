import os

from dotenv import load_dotenv

from application.services.platform import PlatformMonitoring
from infrastructure.adapters.in_memory import InMemoryPlatformRepository
from infrastructure.adapters.postgres import PostgresPlatformRepository
from infrastructure.factories.platform import PlatformAdapterFactory
from infrastructure.database.client import PostgresClient


load_dotenv(".env")

BASE_DIR = "db"
ENV = os.environ["OPEN_DATA_MONITORING_ENV"]

os.environ["PERSISTENCE_MODULE"] = "eventsourcing.sqlite"
os.environ["SQLITE_LOCK_TIMEOUT"] = "10"  # seconds

if ENV == "PROD":  # pragma: no cover
    raise NotImplementedError
elif ENV == "TEST":
    print(f"App environment = {ENV}")
    repository = InMemoryPlatformRepository([])
    app = PlatformMonitoring(
        adapter_factory=PlatformAdapterFactory, repository=repository
    )
else:  # pragma: no cover
    print(f"App environment = {ENV}")
    client = PostgresClient(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host="localhost",
        port=5432,
    )
    repository = PostgresPlatformRepository(client=client)
    app = PlatformMonitoring(
        adapter_factory=PlatformAdapterFactory, repository=repository
    )