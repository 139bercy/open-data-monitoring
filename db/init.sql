CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE TABLE IF NOT EXISTS platforms (
    id uuid PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    name varchar(255) NOT NULL,
    slug varchar(255) NOT NULL UNIQUE,
    type varchar(50) NOT NULL,
    url text NOT NULL,
    organization_id varchar(255) NOT NULL,
    key varchar(255),
    datasets_count int NOT NULL DEFAULT 0,
    last_sync timestamptz,
    last_sync_status text CHECK (
        last_sync_status IN ('success', 'failed', 'pending')
    )
);
COMMENT ON TABLE platforms IS 'Table de stockage des plateformes de données';
COMMENT ON COLUMN platforms.key IS 'Clé secrète pour l''API de la plateforme';
COMMENT ON COLUMN platforms.datasets_count IS 'Dernier nombre de datasets synchronisés';
-- Index pour les recherches courantes
CREATE INDEX IF NOT EXISTS idx_platforms_slug ON platforms (slug);
-- Création d'un type ENUM pour le statut de synchronisation
CREATE TYPE sync_status_type AS enum ('success', 'failed', 'partial_success');
-- Table d'historique des synchronisations
CREATE TABLE IF NOT EXISTS platform_sync_histories (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id uuid NOT NULL REFERENCES platforms (id) ON DELETE CASCADE,
    timestamp timestamptz NOT NULL DEFAULT NOW(),
    status sync_status_type NOT NULL,
    datasets_count int NOT NULL CHECK (datasets_count >= 0)
);
COMMENT ON TABLE platform_sync_histories IS 'Historique des synchronisations des plateformes';
COMMENT ON COLUMN platform_sync_histories.status IS 'Statut de la synchronisation (success/partial_success/failed)';
COMMENT ON COLUMN platform_sync_histories.datasets_count IS 'Nombre de datasets synchronisés lors de cette exécution';
-- Index pour les requêtes courantes
CREATE INDEX IF NOT EXISTS idx_platform_sync_platform_id ON platform_sync_histories (platform_id);
CREATE INDEX IF NOT EXISTS idx_platform_sync_timestamp ON platform_sync_histories (timestamp);
-- Contrainte de temporalité (optionnel)
CREATE INDEX IF NOT EXISTS idx_platform_sync_chrono ON platform_sync_histories (platform_id, timestamp DESC);
CREATE TABLE IF NOT EXISTS datasets (
    id uuid PRIMARY KEY,
    platform_id uuid NOT NULL REFERENCES platforms (id),
    timestamp timestamptz NOT NULL DEFAULT NOW(),
    buid varchar(255) NOT NULL,
    slug varchar(255) NOT NULL,
    page text NOT NULL,
    publisher varchar(255),
    created timestamptz NOT NULL,
    modified timestamptz NOT NULL,
    published bool DEFAULT NULL,
    restricted bool DEFAULT NULL,
    last_sync timestamptz,
    last_sync_status text CHECK (
        last_sync_status IN ('pending', 'success', 'failed')
    ),
    deleted bool DEFAULT FALSE
);
COMMENT ON TABLE datasets IS 'Stockage central des métadonnées de datasets';
COMMENT ON COLUMN datasets.buid IS 'Identifiant unique métier de la source';
COMMENT ON COLUMN datasets.slug IS 'Identifiant lisible pour les URLs';
COMMENT ON COLUMN datasets.last_sync IS 'Dernière synchronisation avec la source';
CREATE INDEX IF NOT EXISTS idx_datasets_slug ON datasets (slug);
CREATE INDEX IF NOT EXISTS idx_datasets_publisher ON datasets (publisher);
CREATE INDEX IF NOT EXISTS idx_datasets_modified ON datasets (modified);
CREATE INDEX IF NOT EXISTS idx_datasets_created ON datasets (created);
CREATE TABLE IF NOT EXISTS dataset_blobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id uuid NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    hash varchar(64) NOT NULL,
    data jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    UNIQUE (dataset_id, hash)
);
COMMENT ON TABLE dataset_blobs IS 'Stockage dédoublonné des métadonnées par dataset';
CREATE TABLE IF NOT EXISTS dataset_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp timestamptz NOT NULL DEFAULT NOW(),
    dataset_id uuid NOT NULL,
    blob_id uuid REFERENCES dataset_blobs(id),
    snapshot jsonb,
    -- Temporairement gardé pour la migration
    checksum varchar(64) NOT NULL,
    downloads_count int,
    api_calls_count int,
    views_count int,
    reuses_count int,
    followers_count int,
    popularity_score float,
    diff jsonb
);
CREATE INDEX IF NOT EXISTS idx_dataset_versions_blob_id ON dataset_versions (blob_id);
COMMENT ON TABLE dataset_versions IS 'Historique des versions des métadonnées';
COMMENT ON COLUMN dataset_versions.blob_id IS 'Référence vers le contenu lourd dédoublonné';
COMMENT ON COLUMN dataset_versions.snapshot IS 'Ancien champ, sera supprimé après migration';
COMMENT ON COLUMN dataset_versions.checksum IS 'Hash SHA-256 du snapshot pour détecter les changements';
CREATE TABLE IF NOT EXISTS dataset_quality (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp timestamptz NOT NULL DEFAULT NOW(),
    dataset_id uuid NOT NULL,
    downloads_count int DEFAULT 0,
    api_calls_count int DEFAULT 0,
    has_description bool DEFAULT FALSE,
    is_slug_valid bool DEFAULT TRUE,
    evaluation_results jsonb
);
COMMENT ON TABLE dataset_quality IS 'Stockage des données de qualité des jeux de données';
COMMENT ON COLUMN dataset_quality.downloads_count IS 'téléchargements du jeu de données depuis sa création';
COMMENT ON COLUMN dataset_quality.api_calls_count IS 'Appels API du jeu de données depuis sa création';
COMMENT ON COLUMN dataset_quality.has_description IS 'Le jeu de données a une description en métadonnées';
COMMENT ON COLUMN dataset_quality.is_slug_valid IS 'L''identifiant du jeu de données ne comporte pas de caractères indésirables (ex: _)';