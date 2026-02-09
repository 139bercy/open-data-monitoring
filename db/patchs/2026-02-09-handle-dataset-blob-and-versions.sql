-- Consolidated Migration: Storage Optimization & Harmonized Metrics
-- Date: 2026-02-09
-- Impact: BREAKING CHANGE (Requires migrate_blobs.py execution)

BEGIN;

-- 1. Datasets: Add deletion tracking and title
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS deleted boolean DEFAULT FALSE;
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS title text;

-- 2. Dataset Quality: Add slug validation and evaluation results
ALTER TABLE dataset_quality 
    ALTER COLUMN downloads_count DROP NOT NULL,
    ALTER COLUMN downloads_count DROP DEFAULT,
    ALTER COLUMN api_calls_count DROP NOT NULL,
    ALTER COLUMN api_calls_count DROP DEFAULT,
    ADD COLUMN IF NOT EXISTS is_slug_valid boolean DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS evaluation_results jsonb,
    ADD CONSTRAINT dataset_quality_dataset_id_key UNIQUE (dataset_id);

COMMENT ON COLUMN dataset_quality.is_slug_valid IS 'L''identifiant du jeu de données ne comporte pas de caractères indésirables (ex: _)';

-- 3. Dataset Blobs: Create deduplicated storage (Per-dataset)
CREATE TABLE IF NOT EXISTS dataset_blobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id uuid NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    hash varchar(64) NOT NULL,
    data jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    UNIQUE (dataset_id, hash)
);

COMMENT ON TABLE dataset_blobs IS 'Stockage dédoublonné des métadonnées par dataset';

-- 4. Dataset Versions: Add metrics and blob reference
ALTER TABLE dataset_versions 
    ADD COLUMN IF NOT EXISTS blob_id uuid REFERENCES dataset_blobs(id),
    ADD COLUMN IF NOT EXISTS views_count int,
    ADD COLUMN IF NOT EXISTS reuses_count int,
    ADD COLUMN IF NOT EXISTS followers_count int,
    ADD COLUMN IF NOT EXISTS popularity_score float,
    ADD COLUMN IF NOT EXISTS diff jsonb,
    ADD COLUMN IF NOT EXISTS title text,
    ADD COLUMN IF NOT EXISTS metadata_volatile jsonb;

-- 5. Performance: Add index for foreign key lookups
CREATE INDEX IF NOT EXISTS idx_dataset_versions_blob_id ON dataset_versions (blob_id);

COMMENT ON COLUMN dataset_versions.blob_id IS 'Référence vers le contenu lourd dédoublonné';
COMMENT ON COLUMN dataset_versions.diff IS 'Delta par rapport à la version précédente (Audit Log)';

COMMIT;
