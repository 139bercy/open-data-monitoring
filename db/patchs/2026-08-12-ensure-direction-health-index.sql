-- Patch: Ensure unique index on direction_health_stats_view to support REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX IF NOT EXISTS idx_direction_health_stats_view_direction
ON direction_health_stats_view (direction);
