#!/bin/bash

set -euo pipefail

CONFIG_FILE="stats/config.json"
DATE=$(date +"%Y-%m-%d")

FREQUENCY=${1:-daily}  # Default = daily
PORT=$(jq -r '.port' "$CONFIG_FILE")
DATABASE=$(jq -r '.database' "$CONFIG_FILE")

echo "📄 Use config file: $CONFIG_FILE"
echo "📦 Use database $DATABASE:$PORT"
echo "⏲️ Frequency: $FREQUENCY"

jq -c --arg freq "$FREQUENCY" '.jobs[] | select(.frequency == $freq)' "$CONFIG_FILE" | while read -r job; do
  SQL_FILE=$(echo "$job" | jq -r '.sql')
  OUTPUT_FILE=$(echo "$job" | jq -r '.output')
  DATASET_UID=$(echo "$job" | jq -r '.dataset_uid')
  LABEL=$(echo "$job" | jq -r '.label')

  OUTPUT_PATH="${DATE}-${OUTPUT_FILE}"

  echo "▶️  [$LABEL] SQL Query : $SQL_FILE → $OUTPUT_PATH"
  psql -U postgres -d $DATABASE -h localhost -p "$PORT" -At -f "$SQL_FILE" -o "$OUTPUT_PATH"
  echo "✅  Export to $OUTPUT_PATH"
  echo "☁️  Send to ODS platform (dataset UID : $DATASET_UID), $OUTPUT_FILE"
  python stats/push_stats.py --file "$OUTPUT_PATH" --dataset_uid "$DATASET_UID"
  echo ""
done
