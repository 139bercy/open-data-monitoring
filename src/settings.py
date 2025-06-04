import os

from dotenv import load_dotenv

from application.services.platform import PlatformMonitoring
from infrastructure.adapters.in_memory import InMemoryPlatformRepository
from infrastructure.factories.platform import PlatformAdapterFactory

load_dotenv(".env")

BASE_DIR = "db"
ENV = os.environ["OPEN_DATA_MONITORING_ENV"]

os.environ["PERSISTENCE_MODULE"] = "eventsourcing.sqlite"
os.environ["SQLITE_LOCK_TIMEOUT"] = "10"  # seconds

if ENV == "PROD":  # pragma: no cover
    print(f"App environment = {ENV}")
    raise NotImplementedError
elif ENV == "TEST":
    print(f"App environment = {ENV}")
    repository = InMemoryPlatformRepository([])
    app = PlatformMonitoring(
        adapter_factory=PlatformAdapterFactory, repository=repository
    )
else:  # pragma: no cover
    print(f"App environment = {ENV}")
    raise NotImplementedError
