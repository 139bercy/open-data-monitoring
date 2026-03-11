-- Merged patch for health metrics and semantic obsolescence
-- Includes: health scores, evaluated_blob_id, and cleanup of legacy columns

-- 1. Metadata for semantic obsolescence (replaces evaluated_snapshot_id)
ALTER TABLE dataset_quality DROP COLUMN IF EXISTS evaluated_snapshot_id;
ALTER TABLE dataset_quality ADD COLUMN IF NOT EXISTS evaluated_blob_id uuid REFERENCES dataset_blobs(id) ON DELETE SET NULL;
COMMENT ON COLUMN dataset_quality.evaluated_blob_id IS 'ID du blob (contenu qualitatif) utilisé pour le dernier audit LLM';

-- 2. Health score columns
ALTER TABLE dataset_quality ADD COLUMN IF NOT EXISTS health_score DOUBLE PRECISION;
ALTER TABLE dataset_quality ADD COLUMN IF NOT EXISTS health_quality_score DOUBLE PRECISION;
ALTER TABLE dataset_quality ADD COLUMN IF NOT EXISTS health_freshness_score DOUBLE PRECISION;
ALTER TABLE dataset_quality ADD COLUMN IF NOT EXISTS health_engagement_score DOUBLE PRECISION;

COMMENT ON COLUMN dataset_quality.health_score IS 'Score global de santé du jeu de données (0-100)';
COMMENT ON COLUMN dataset_quality.health_quality_score IS 'Score de qualité intrinsèque (0-100)';
COMMENT ON COLUMN dataset_quality.health_freshness_score IS 'Score de fraîcheur temporelle (0-100)';
COMMENT ON COLUMN dataset_quality.health_engagement_score IS 'Score d''engagement et usage (0-100)';
