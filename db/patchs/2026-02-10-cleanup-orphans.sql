-- Cleanup Migration Orphans
-- Supprime les versions qui ne sont plus rattachées à un dataset valide
-- pour éviter les violations de clé étrangère lors de la migration vers dataset_blobs.

BEGIN;

--DELETE FROM dataset_versions
SELECT count(*) FROM dataset_versions
WHERE dataset_id NOT IN (SELECT id FROM datasets);

COMMIT;
