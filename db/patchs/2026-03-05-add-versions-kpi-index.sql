-- Migration: Add index for faster KPI calculations
-- Description: Improve performance of DISTINCT ON queries by dataset_id
-- Author: Antigravity

CREATE INDEX IF NOT EXISTS idx_dataset_versions_dataset_id_timestamp ON dataset_versions(dataset_id, timestamp DESC);
