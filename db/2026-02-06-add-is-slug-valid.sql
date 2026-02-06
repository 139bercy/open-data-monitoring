-- Migration patch: Add is_slug_valid to dataset_quality
-- Date: 2026-02-06
ALTER TABLE dataset_quality
ADD COLUMN IF NOT EXISTS is_slug_valid boolean DEFAULT TRUE;
COMMENT ON COLUMN dataset_quality.is_slug_valid IS 'L''identifiant du jeu de données ne comporte pas de caractères indésirables (ex: _)';