#!/bin/bash

# Check if a dump file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_dump_file>"
    exit 1
fi

DUMP_FILE="$1"

# Check if file exists
if [ ! -f "$DUMP_FILE" ]; then
    echo "Error: File '$DUMP_FILE' not found."
    exit 1
fi

echo "Cleaning up the database schema..."
psql -U postgres -h localhost -d odm -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

if [ $? -ne 0 ]; then
    echo "Failed to clean the database schema."
    exit 1
fi

echo "Restoring from $DUMP_FILE..."
pg_restore -h localhost -U postgres -d odm "$DUMP_FILE" -v

if [ $? -eq 0 ]; then
    echo "Database restoration completed successfully."
else
    echo "Database restoration finished with some errors (check logs above)."
fi
