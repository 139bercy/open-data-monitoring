ALTER TABLE dataset_versions ADD COLUMN downloads_count integer DEFAULT NULL;
UPDATE dataset_versions dv
SET downloads_count = (dv.snapshot ->> 'download_count')::int
FROM datasets d JOIN platforms p ON p.id = d.platform_id
WHERE dv.dataset_id = d.id AND p.type = 'opendatasoft' AND dv.snapshot ? 'download_count';

ALTER TABLE dataset_versions ADD COLUMN api_calls_count integer DEFAULT NULL;
UPDATE dataset_versions dv
SET api_calls_count = (dv.snapshot ->> 'api_call_count')::int
FROM datasets d JOIN platforms p ON p.id = d.platform_id
WHERE dv.dataset_id = d.id AND p.type = 'opendatasoft' AND dv.snapshot ? 'api_call_count';

-- SELECT p.name, d.slug, dv.downloads_count, dv.api_calls_count
-- FROM dataset_versions dv JOIN datasets d ON dv.dataset_id = d.id JOIN platforms p ON d.platform_id = p.id
-- WHERE p.type = 'opendatasoft'
-- ORDER BY api_calls_count DESC NULLS LAST
-- LIMIT 10;
l