-- View: normalized_datasets
CREATE OR REPLACE VIEW normalized_datasets AS
SELECT
    id,
    slug,
    CASE
        WHEN publisher IS NULL OR publisher = '' THEN 'Inconnu'
        ELSE publisher
    END AS normalized_publisher,
    modified,
    published,
    deleted,
    restricted
FROM datasets;

-- View: direction_health_stats_view
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'direction_health_stats_view') THEN
        DROP MATERIALIZED VIEW direction_health_stats_view;
    ELSIF EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'direction_health_stats_view') THEN
        DROP VIEW direction_health_stats_view;
    END IF;
END $$;

CREATE MATERIALIZED VIEW direction_health_stats_view AS
WITH latest_quality AS (
    SELECT DISTINCT ON (dataset_id)
        dataset_id,
        health_score,
        health_quality_score,
        health_freshness_score,
        health_engagement_score,
        evaluated_blob_id
    FROM dataset_quality
    ORDER BY dataset_id, timestamp DESC
),
dataset_scores AS (
    SELECT
        d.normalized_publisher as direction,
        dq.health_quality_score as quality_score,
        dq.health_freshness_score as freshness_score,
        dq.health_engagement_score as engagement_score,
        dq.health_score as global_score
    FROM normalized_datasets d
    JOIN latest_quality dq ON d.id = dq.dataset_id
    WHERE d.deleted IS FALSE 
      AND d.published IS TRUE 
      AND d.restricted IS FALSE
      AND dq.evaluated_blob_id IS NOT NULL  -- Exclure les datasets sans version évaluée
)
SELECT
    direction,
    ROUND(AVG(quality_score)::numeric, 2) as score_quality,
    ROUND(AVG(freshness_score)::numeric, 2) as score_freshness,
    ROUND(AVG(engagement_score)::numeric, 2) as score_engagement,
    ROUND(AVG(global_score)::numeric, 2) as score_global,
    COUNT(*) as dataset_count,
    COUNT(*) FILTER (WHERE global_score < 50) as unhealthy_count
FROM dataset_scores
GROUP BY direction;

CREATE UNIQUE INDEX IF NOT EXISTS idx_direction_health_stats_view_direction ON direction_health_stats_view (direction);
