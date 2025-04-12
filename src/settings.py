import os

from dotenv import load_dotenv

from application.projections import TinyDbPlatformRepository
from application.services import DataMonitoring
from infrastructure.factory import AdapterFactory

load_dotenv(".env")

BASE_DIR = "db"
ENV = os.environ["OPEN_DATA_MONITORING_ENV"]

os.environ["PERSISTENCE_MODULE"] = "eventsourcing.sqlite"
os.environ["SQLITE_LOCK_TIMEOUT"] = "10"  # seconds

if ENV == "PROD":
    print(f"App environment = {ENV}")
    os.environ["SQLITE_DBNAME"] = f"{BASE_DIR}/writes.db"
    READS_DB_NAME = f"{BASE_DIR}/reads.json"
    repository = TinyDbPlatformRepository(READS_DB_NAME)
    app = DataMonitoring(
        adapter_factory=AdapterFactory, repository=repository
    )
elif ENV == "TEST":
    print(f"App environment = {ENV}")
    os.environ["SQLITE_DBNAME"] = ":memory:"
    READS_DB_NAME = f"{BASE_DIR}/test.json"
    repository = TinyDbPlatformRepository(READS_DB_NAME)
    app = DataMonitoring(
        adapter_factory=AdapterFactory, repository=repository
    )
else:
    print(f"App environment = {ENV}")
    os.environ["SQLITE_DBNAME"] = f"{BASE_DIR}/writes-dev.db"
    READS_DB_NAME = f"{BASE_DIR}/reads-dev.json"
    repository = TinyDbPlatformRepository(READS_DB_NAME)
    app = DataMonitoring(
        adapter_factory=AdapterFactory, repository=repository
    )