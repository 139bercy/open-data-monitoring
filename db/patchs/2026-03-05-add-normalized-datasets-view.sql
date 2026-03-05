-- Migration: Add normalized_datasets view
-- Description: Unify publisher names to compute global metrics accurately.
-- Author: Antigravity

CREATE OR REPLACE VIEW normalized_datasets AS
SELECT
    id,
    slug,
    CASE
        WHEN publisher ILIKE 'DGFIP' THEN 'DGFiP'
        WHEN publisher ILIKE 'DGCCRF%' THEN 'DGCCRF'
        WHEN publisher ILIKE 'DGE' THEN 'DGE'
        WHEN publisher ILIKE 'DGTRESOR' THEN 'DG Trésor'
        WHEN publisher ILIKE 'DGDDI' THEN 'DGDDI'
        WHEN publisher ILIKE 'DAJ' THEN 'DAJ'
        WHEN publisher ILIKE 'DAE' THEN 'DAE'
        WHEN publisher ILIKE 'DGAFP' THEN 'DGAFP'
        WHEN publisher ILIKE 'DGT' THEN 'DG Trésor'
        WHEN publisher IS NULL OR publisher = '' THEN 'Inconnu'
        ELSE publisher
    END as normalized_publisher,
    modified,
    published,
    deleted
FROM datasets;

COMMENT ON VIEW normalized_datasets IS 'View normalizing dataset publishers to unified Directions.';
