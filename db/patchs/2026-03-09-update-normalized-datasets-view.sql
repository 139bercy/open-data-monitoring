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
        WHEN publisher ilike 'Direction Générale du Trésor' THEN 'DG Trésor'
        WHEN publisher ILIKE 'Bercy Hub - Mission Open Data' THEN 'Bercy Hub'
        WHEN publisher IS NULL OR publisher = '' THEN 'Inconnu'
        ELSE publisher
    END AS normalized_publisher,
    modified,
    published,
    deleted,
    restricted
FROM datasets;
