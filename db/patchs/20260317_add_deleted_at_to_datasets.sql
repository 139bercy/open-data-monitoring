-- Lifecycle management (Archiving & Cold Storage)
-- Added on 2026-03-17

ALTER TABLE datasets ADD COLUMN IF NOT EXISTS deleted_at timestamptz;
COMMENT ON COLUMN datasets.deleted_at IS 'Timestamp when the dataset was marked as deleted from source.';
