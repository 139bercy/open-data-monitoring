CREATE TABLE IF NOT EXISTS dataset_quality
(
    id              uuid PRIMARY KEY     DEFAULT gen_random_uuid(),
    timestamp       timestamptz NOT NULL DEFAULT NOW(),
    dataset_id      uuid        NOT NULL,
    downloads_count int         NOT NULL DEFAULT 0,
    api_calls_count int         NOT NULL DEFAULT 0,
    has_description bool        NOT NULL DEFAULT FALSE
);

COMMENT ON TABLE dataset_quality IS 'Stockage des données de qualité des jeux de données';
COMMENT ON COLUMN dataset_quality.downloads_count IS 'téléchargements du jeu de données depuis sa création';
COMMENT ON COLUMN dataset_quality.api_calls_count IS 'Appels API du jeu de données depuis sa création';
COMMENT ON COLUMN dataset_quality.has_description IS 'Le jeu de données a une description en métadonnées';