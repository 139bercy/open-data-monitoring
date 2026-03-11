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
WITH latest_version_info AS (
    SELECT DISTINCT ON (dataset_id)
        dataset_id,
        blob_id,
        views_count,
        reuses_count,
        followers_count,
        popularity_score
    FROM dataset_versions
    ORDER BY dataset_id, timestamp DESC
),
latest_quality AS (
    SELECT DISTINCT ON (dataset_id)
        dataset_id,
        has_description,
        is_slug_valid,
        syntax_change_score,
        api_calls_count,
        downloads_count
    FROM dataset_quality
    ORDER BY dataset_id, timestamp DESC
),
dataset_thresholds AS (
    SELECT
        b.dataset_id,
        CASE
            WHEN COALESCE(b.data->>'frequency', b.data->'metas'->'default'->>'accrual_periodicity', 'unknown') = 'daily' THEN 2
            WHEN COALESCE(b.data->>'frequency', b.data->'metas'->'default'->>'accrual_periodicity', 'unknown') = 'continuous' THEN 2
            WHEN COALESCE(b.data->>'frequency', b.data->'metas'->'default'->>'accrual_periodicity', 'unknown') = 'weekly' THEN 9
            WHEN COALESCE(b.data->>'frequency', b.data->'metas'->'default'->>'accrual_periodicity', 'unknown') = 'monthly' THEN 37
            WHEN COALESCE(b.data->>'frequency', b.data->'metas'->'default'->>'accrual_periodicity', 'unknown') = 'quarterly' THEN 105
            WHEN COALESCE(b.data->>'frequency', b.data->'metas'->'default'->>'accrual_periodicity', 'unknown') = 'semiannual' THEN 210
            WHEN COALESCE(b.data->>'frequency', b.data->'metas'->'default'->>'accrual_periodicity', 'unknown') = 'annual' THEN 395
            WHEN COALESCE(b.data->>'frequency', b.data->'metas'->'default'->>'accrual_periodicity', 'unknown') = 'punctual' THEN 3650
            ELSE 90 -- Default unknown
        END as days_limit
    FROM latest_version_info v
    JOIN dataset_blobs b ON v.blob_id = b.id
),
raw_scores AS (
    SELECT
        d.id,
        d.normalized_publisher as direction,
        v.blob_id,
        -- Quality Score (0-100)
        (
            CASE WHEN q.has_description THEN 40 ELSE 0 END +
            CASE WHEN q.is_slug_valid THEN 20 ELSE 0 END +
            COALESCE(q.syntax_change_score, 0) * 0.4
        ) as quality_score,
        -- Freshness Score (0-100) - Relative to expected frequency
        CASE
            WHEN (EXTRACT(EPOCH FROM (NOW() -
                COALESCE(
                    NULLIF(b.data->'metas'->'default'->>'modified', '')::timestamptz,
                    d.modified
                )
            )) / 86400) <= t.days_limit THEN 100
            WHEN (EXTRACT(EPOCH FROM (NOW() -
                COALESCE(
                    NULLIF(b.data->'metas'->'default'->>'modified', '')::timestamptz,
                    d.modified
                )
            )) / 86400) <= t.days_limit * 2 THEN 50
            ELSE 0
        END as freshness_score,
        -- Engagement Score (0-100) - Log weighted
        ROUND(
            GREATEST(0, LEAST(100,
                LN(1 + COALESCE(v.views_count, 0)) * 5 +
                LN(1 + COALESCE(q.api_calls_count, 0)) * 3 +
                LN(1 + COALESCE(v.reuses_count, 0)) * 20
            ))
        ) as engagement_score
    FROM normalized_datasets d
    LEFT JOIN latest_quality q ON d.id = q.dataset_id
    LEFT JOIN latest_version_info v ON d.id = v.dataset_id
    LEFT JOIN dataset_thresholds t ON d.id = t.dataset_id
    LEFT JOIN dataset_blobs b ON v.blob_id = b.id
    WHERE d.deleted IS FALSE AND d.published IS TRUE AND d.restricted IS FALSE
),
dataset_scores AS (
    SELECT
        direction,
        quality_score,
        freshness_score,
        engagement_score,
        (quality_score * 0.5 + freshness_score * 0.3 + engagement_score * 0.2) as global_score
    FROM raw_scores
    WHERE blob_id IS NOT NULL  -- Exclure les datasets sans version connue (scores non fiables)
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
