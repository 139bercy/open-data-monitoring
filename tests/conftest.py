import os

# Use SQLite for persistence.
os.environ['PERSISTENCE_MODULE'] = 'eventsourcing.sqlite'

# or use an in-memory DB with cache not shared, only works with single thread;
os.environ['SQLITE_DBNAME'] = ':memory:'
