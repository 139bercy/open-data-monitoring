---
description: Apply storage optimization migration and backfill blobs
---

This workflow applies the database patches and runs the migration script to deduplicate snapshots into blobs.

1. Ensure the virtual environment is activated.
2. Apply the SQL patches from `db/patchs/`.
// turbo
3. Run the blob migration script:
   ```bash
   python scripts/migrate_blobs.py
   ```
4. Run the storage optimization tests to verify:
   ```bash
   pytest tests/test_storage_optimization.py
   ```
5. Run the full test suite to ensure no regressions:
   ```bash
   pytest tests/
   ```
