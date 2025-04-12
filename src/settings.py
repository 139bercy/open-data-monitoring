import os

from dotenv import load_dotenv

from application.projections import TinyDbPlatformRepository
from application.services import DataMonitoring
from infrastructure.factory import AdapterFactory

load_dotenv(".env")

BASE_DIR = "db"
ENV = os.environ["ENV"]

os.environ["PERSISTENCE_MODULE"] = "eventsourcing.sqlite"

if ENV == "PROD":
    print(f"App environment = {ENV}")
    os.environ["SQLITE_DBNAME"] = f"{BASE_DIR}/writes.db"
    READS_DB_NAME = f"{BASE_DIR}/reads.json"
else:
    print(f"App environment = {ENV}")
    os.environ["SQLITE_DBNAME"] = f"{BASE_DIR}/writes-dev.db"
    READS_DB_NAME = f"{BASE_DIR}/reads-dev.json"

repository = TinyDbPlatformRepository(READS_DB_NAME)
app = DataMonitoring(
    adapter_factory=AdapterFactory, repository=repository)

# or use an in-memory DB with cache not shared, only works with single thread;
# os.environ['SQLITE_DBNAME'] = ':memory:'

# or use an unnamed in-memory DB with shared cache, works with multiple threads;
# os.environ['SQLITE_DBNAME'] = 'file::memory:?mode=memory&cache=shared'

# or use a named in-memory DB with shared cache, to create distinct databases.
# os.environ['SQLITE_DBNAME'] = 'file:application1?mode=memory&cache=shared'

# Set optional lock timeout (default 5s).
os.environ["SQLITE_LOCK_TIMEOUT"] = "10"  # seconds
