---
description: Inspect a dataset state in the database
---

This workflow helps verify why a dataset is versioning (or not) and checks the integrity of its blobs.

1. Find the dataset ID if unknown:
   ```bash
   # Use psql to find the dataset by slug
   # docker exec -it open-data-monitoring-db psql -U postgres -d odm -c "SELECT id FROM datasets WHERE slug = 'YOUR_SLUG';"
   ```
2. Check the version history and blob links:
   ```bash
   # SELECT v.timestamp, v.checksum, v.blob_id, v.title FROM dataset_versions v WHERE dataset_id = 'UUID' ORDER BY timestamp DESC;
   ```
3. Run the verification script:
   ```bash
   python scripts/verify_migration.py
   ```
4. Check recent logs for versioning decisions:
   ```bash
   grep "Version check for" app.log | tail -n 20
   ```
