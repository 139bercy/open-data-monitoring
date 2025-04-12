import os


# Use SQLite for persistence.
os.environ["PERSISTENCE_MODULE"] = "eventsourcing.sqlite"

# Configure SQLite database URI. Either use a file-based DB;
os.environ["SQLITE_DBNAME"] = "sqlite-db"

# or use an in-memory DB with cache not shared, only works with single thread;
os.environ["SQLITE_DBNAME"] = ":memory:"

# or use an unnamed in-memory DB with shared cache, works with multiple threads;
os.environ["SQLITE_DBNAME"] = "file::memory:?mode=memory&cache=shared"

# or use a named in-memory DB with shared cache, to create distinct databases.
os.environ["SQLITE_DBNAME"] = "file:application1?mode=memory&cache=shared"

# Set optional lock timeout (default 5s).
os.environ["SQLITE_LOCK_TIMEOUT"] = "10"  # seconds
