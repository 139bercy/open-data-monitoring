import os

from dotenv import load_dotenv

from application.queries.platform import TinyDbPlatformRepository
from application.services.platform import PlatformMonitoring
from infrastructure.factories.platform import PlatformAdapterFactory

load_dotenv(".env")

BASE_DIR = "db"
ENV = os.environ["OPEN_DATA_MONITORING_ENV"]

os.environ["PERSISTENCE_MODULE"] = "eventsourcing.sqlite"
os.environ["SQLITE_LOCK_TIMEOUT"] = "10"  # seconds

if ENV == "PROD":  # pragma: no cover
    print(f"App environment = {ENV}")
    os.environ["SQLITE_DBNAME"] = f"{BASE_DIR}/prod/writes.db"
    READS_DB_NAME = f"{BASE_DIR}/prod/reads.json"
    repository = TinyDbPlatformRepository(READS_DB_NAME)
    app = PlatformMonitoring(adapter_factory=PlatformAdapterFactory, repository=repository)
elif ENV == "TEST":
    print(f"App environment = {ENV}")
    os.environ["SQLITE_DBNAME"] = ":memory:"
    READS_DB_NAME = f"{BASE_DIR}/test/test.json"
    repository = TinyDbPlatformRepository(READS_DB_NAME)
    app = PlatformMonitoring(adapter_factory=PlatformAdapterFactory, repository=repository)
else:  # pragma: no cover
    print(f"App environment = {ENV}")
    os.environ["SQLITE_DBNAME"] = f"{BASE_DIR}/dev/writes-dev.db"
    READS_DB_NAME = f"{BASE_DIR}/dev/reads-dev.json"
    repository = TinyDbPlatformRepository(READS_DB_NAME)
    app = PlatformMonitoring(adapter_factory=PlatformAdapterFactory, repository=repository)
