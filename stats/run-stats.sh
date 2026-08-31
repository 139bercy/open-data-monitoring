#!/bin/bash

set -euo pipefail

CONFIG_FILE="stats/config.json"
DATE=$(date +"%Y-%m-%d")
PUSH_ENABLED=true
TARGET=""

PYTHON_CMD="python3"
if [ -f "venv/bin/python" ]; then
  PYTHON_CMD="venv/bin/python"
fi

# Function to display the catalog of indicators from code/config
show_docs() {
  echo "# 📊 Catalogue du Pipeline de Statistiques"
  echo ""
  echo "Ce rapport liste les indicateurs automatisés définis dans \`$CONFIG_FILE\`."
  echo ""
  echo "| Nom | Fréquence | Label | Export SQL | Compute SQL |"
  echo "| :--- | :--- | :--- | :--- | :--- |"
  jq -r '.jobs[] | "| `\(.name)` | \(.frequency) | \(.label) | \(.export_sql) | \(.compute_sql // "-") |"' "$CONFIG_FILE"
}


# Parse arguments
for arg in "$@"; do
  case $arg in
    --no-push)
      PUSH_ENABLED=false
      shift
      ;;
    --list)
      show_docs
      exit 0
      ;;
    *)
      TARGET="$arg"
      shift
      ;;
  esac
done

if [ -z "$TARGET" ]; then
  echo "Usage: ./stats/run-stats.sh <frequency|job_name> [--no-push] [--list]"
  exit 1
fi

if [ -f ".env" ]; then
  # Load relevant DB credentials from .env if present
  set -a
  source .env
  set +a
fi

export PGPASSWORD="${PGPASSWORD:-${DB_PASSWORD:-}}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"

PORT=$(jq -r '.port' "$CONFIG_FILE")
DATABASE=$(jq -r '.database' "$CONFIG_FILE")

echo "📄 Use config file: $CONFIG_FILE"
echo "📦 Use database $DATABASE:$PORT"
echo "⏲️  Target: $TARGET"
if [ "$PUSH_ENABLED" = false ]; then
  echo "🚫 Mode --no-push active : les fichiers ne seront pas envoyés."
fi

# Filter jobs by frequency OR name
jq -c --arg target "$TARGET" '.jobs[] | select(.frequency == $target or .name == $target)' "$CONFIG_FILE" | while read -r job; do
  COMPUTE_SQL=$(echo "$job" | jq -r '.compute_sql // empty')
  EXPORT_SQL=$(echo "$job" | jq -r '.export_sql')
  OUTPUT_FILE=$(echo "$job" | jq -r '.output')
  DATASET_UID=$(echo "$job" | jq -r '.dataset_uid')
  LABEL=$(echo "$job" | jq -r '.label')

  OUTPUT_PATH="${DATE}-${OUTPUT_FILE}"

  echo "▶️  [$LABEL] SQL Queries"

  if [ -n "$COMPUTE_SQL" ]; then
    echo "    ⚙️  Compute : $COMPUTE_SQL"
    psql -X -w -U "$DB_USER" -d "$DATABASE" -h "$DB_HOST" -p "$PORT" -f "$COMPUTE_SQL" || true
  fi

  echo "    💾 Export  : $EXPORT_SQL → $OUTPUT_PATH"
  EXPORT_QUERY=$(cat "$EXPORT_SQL" | grep -v '^--' | tr '\n' ' ' | sed 's/;[[:space:]]*$//')
  psql -X -w -U "$DB_USER" -d "$DATABASE" -h "$DB_HOST" -p "$PORT" -c "\\copy ($EXPORT_QUERY) TO STDOUT WITH CSV HEADER" > "$OUTPUT_PATH" || true
  echo "✅  Export to $OUTPUT_PATH"

  PUSH_ARGS=("--file" "$OUTPUT_PATH" "--dataset_uid" "$DATASET_UID")
  if [ "$PUSH_ENABLED" = false ]; then
      PUSH_ARGS+=("--no-push")
  fi

  echo "☁️  Executing push command: $PYTHON_CMD stats/push_stats.py ${PUSH_ARGS[*]}"
  "$PYTHON_CMD" stats/push_stats.py "${PUSH_ARGS[@]}"
  echo ""
done
