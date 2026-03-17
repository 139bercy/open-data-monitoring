-- Remove legacy snapshot column
-- Added on 2026-03-17

ALTER TABLE dataset_versions DROP COLUMN IF EXISTS snapshot;
