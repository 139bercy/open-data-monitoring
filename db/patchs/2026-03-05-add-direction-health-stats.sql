-- Migration: Add direction_health_stats read-model
-- Description: Create a table for aggregated health scores by direction (publisher)
-- Author: Antigravity

CREATE TABLE IF NOT EXISTS direction_health_stats (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    direction text NOT NULL,
    score_quality double precision NOT NULL DEFAULT 0,
    score_freshness double precision NOT NULL DEFAULT 0,
    score_engagement double precision NOT NULL DEFAULT 0,
    score_global double precision NOT NULL DEFAULT 0,
    dataset_count integer NOT NULL DEFAULT 0,
    unhealthy_count integer NOT NULL DEFAULT 0,
    timestamp timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_direction_health_stats_direction ON direction_health_stats(direction);
CREATE INDEX IF NOT EXISTS idx_direction_health_stats_timestamp ON direction_health_stats(timestamp);

COMMENT ON TABLE direction_health_stats IS 'Read-model for the Heatmap, aggregating MBI scores by direction.';
