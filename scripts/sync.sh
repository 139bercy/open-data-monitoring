#!/bin/bash

# Sync remote PostgreSQL DB to local DB

set -e

if [ "$#" -ne 3 ]; then
  echo "❌  Usage: $0 <SERVER> <SOURCE_PORT> <DEST_PORT>"
  exit 1
fi

SERVER=$1
SOURCE_PORT=$2
DEST_PORT=$3
DATE=$(date +"%Y-%m-%d")
DUMP_FILE="odm-${DATE}.dump"
BACKUP_FILE="odm-${DATE}-backup.dump"

echo "Dumping remote database from $SERVER:$SOURCE_PORT..."
ssh "$SERVER" "sudo -u postgres pg_dump -h localhost -p $SOURCE_PORT -d odm -F c" > "$DUMP_FILE"

echo "Creating local backup of current database..."
pg_dump -h localhost -U postgres -d odm -p "$DEST_PORT" -F c -f "$BACKUP_FILE"

echo "Restoring remote dump into local database..."
pg_restore -h localhost -U postgres -d odm -p "$DEST_PORT" -c "$DUMP_FILE"

echo "Sync complete."
