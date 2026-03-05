-- Export pur des données MBI (Monitoring Business Indicators)
SELECT
    direction,
    score_quality,
    score_freshness,
    score_engagement,
    score_global,
    dataset_count,
    unhealthy_count
FROM direction_health_stats
ORDER BY score_global DESC;
