-- ============================================================================
-- Unified Impact Score - Business Logic
-- ============================================================================
-- Ce script identifie le Top 20 des datasets les plus "impactants" de la semaine.
-- Il normalise les différences entre plateformes pour permettre une comparaison équitable.
--
-- LOGIQUE DE CALCUL (Unified Impact Score) :
-- 1. SCORE D'ACTIVITÉ (Pondéré + Échelle Logarithmique) :
--    - Poids : 1.0 par Vue, 2.0 par Téléchargement, 0.5 par Appel API.
--    - Application de LN(1 + x) * 15 pour aplatir les outliers.
-- 2. SCORE D'ENGAGEMENT : +30 pts / nouveau Follower.
-- 3. SCORE DE CRÉATION DE VALEUR : +80 pts / nouvelle Réutilisation.
-- 4. BONUS DE FRAÎCHEUR : +10 pts si créé < 90 jours.
-- ============================================================================

\COPY (WITH weekly_delta AS (SELECT d.id, d.slug, d.created, p.type as platform_type, p.name as platform, MIN(dv.views_count) as start_views, MAX(dv.views_count) as end_views, MIN(dv.api_calls_count) as start_api, MAX(dv.api_calls_count) as end_api, MIN(dv.downloads_count) as start_dl, MAX(dv.downloads_count) as end_dl, MIN(dv.followers_count) as start_followers, MAX(dv.followers_count) as end_followers, MIN(dv.reuses_count) as start_reuses, MAX(dv.reuses_count) as end_reuses FROM dataset_versions dv JOIN datasets d ON d.id = dv.dataset_id JOIN platforms p ON p.id = d.platform_id WHERE dv.timestamp >= CURRENT_DATE - INTERVAL '1 week' AND d.deleted IS FALSE GROUP BY d.id, d.slug, d.created, p.type, p.name), scored_datasets AS (SELECT slug, platform, platform_type, CASE WHEN platform_type = 'opendatasoft' THEN (end_dl - start_dl) * 2.0 + (end_api - start_api) * 0.5 ELSE (end_views - start_views) * 1.0 END as weighted_activity, (end_followers - start_followers) as followers_gain, (end_reuses - start_reuses) as reuses_gain, CASE WHEN created >= CURRENT_DATE - INTERVAL '90 days' THEN 10 ELSE 0 END as freshness_bonus FROM weekly_delta) SELECT slug, platform, ROUND((LN(1 + GREATEST(0, weighted_activity)) * 15) + (GREATEST(0, followers_gain) * 30) + (GREATEST(0, reuses_gain) * 80) + freshness_bonus, 2) as unified_impact_score, weighted_activity as raw_activity_index, followers_gain as weekly_followers_gain, reuses_gain as weekly_reuses_gain, platform_type FROM scored_datasets WHERE (weighted_activity > 0 OR followers_gain > 0 OR reuses_gain > 0) ORDER BY unified_impact_score DESC LIMIT 20) TO STDOUT WITH CSV HEADER;
