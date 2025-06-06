CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS platforms (
     id UUID PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     slug VARCHAR(255) NOT NULL UNIQUE,
     type VARCHAR(50) NOT NULL,
     url TEXT NOT NULL,
     organization_id VARCHAR(255) NOT NULL,
     key VARCHAR(255),
     datasets_count INT NOT NULL DEFAULT 0,
     last_sync TIMESTAMPTZ,
     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE platforms IS 'Table de stockage des plateformes de données';
COMMENT ON COLUMN platforms.key IS 'Clé secrète pour l''API de la plateforme';
COMMENT ON COLUMN platforms.datasets_count IS 'Dernier nombre de datasets synchronisés';

-- Index pour les recherches courantes
CREATE INDEX IF NOT EXISTS idx_platforms_slug ON platforms(slug);

-- Création d'un type ENUM pour le statut de synchronisation
CREATE TYPE sync_status_type AS ENUM ('success', 'failed', 'partial_success');

-- Table d'historique des synchronisations
CREATE TABLE IF NOT EXISTS platform_sync_histories (
   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
   platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
   timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
   status sync_status_type NOT NULL,
   datasets_count INT NOT NULL CHECK (datasets_count >= 0),
   created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE platform_sync_histories IS 'Historique des synchronisations des plateformes';
COMMENT ON COLUMN platform_sync_histories.status IS 'Statut de la synchronisation (success/partial_success/failed)';
COMMENT ON COLUMN platform_sync_histories.datasets_count IS 'Nombre de datasets synchronisés lors de cette exécution';

-- Index pour les requêtes courantes
CREATE INDEX IF NOT EXISTS idx_platform_sync_platform_id ON platform_sync_histories(platform_id);
CREATE INDEX IF NOT EXISTS idx_platform_sync_timestamp ON platform_sync_histories(timestamp);

-- Contrainte de temporalité (optionnel)
CREATE INDEX IF NOT EXISTS idx_platform_sync_chrono ON platform_sync_histories(platform_id, timestamp DESC);


CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY,
    platform_id UUID NOT NULL REFERENCES platforms(id),
    buid VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    page TEXT NOT NULL,
    publisher VARCHAR(255) NOT NULL,
    created TIMESTAMPTZ NOT NULL,
    modified TIMESTAMPTZ NOT NULL,
    last_sync TIMESTAMPTZ
);

COMMENT ON TABLE datasets IS 'Stockage central des métadonnées de datasets';
COMMENT ON COLUMN datasets.buid IS 'Identifiant unique métier de la source';
COMMENT ON COLUMN datasets.slug IS 'Identifiant lisible pour les URLs';
COMMENT ON COLUMN datasets.last_sync IS 'Dernière synchronisation avec la source';

-- Indexes stratégiques
CREATE INDEX IF NOT EXISTS idx_datasets_slug ON datasets(slug);
CREATE INDEX IF NOT EXISTS idx_datasets_publisher ON datasets(publisher);
CREATE INDEX IF NOT EXISTS idx_datasets_modified ON datasets(modified);
CREATE INDEX IF NOT EXISTS idx_datasets_created ON datasets(created);

-- Table de liaison pour le versioning
CREATE TABLE IF NOT EXISTS dataset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dataset_id UUID NOT NULL,
--     dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    snapshot JSONB NOT NULL,
    checksum VARCHAR(64) NOT NULL
);

COMMENT ON TABLE dataset_versions IS 'Historique des versions des métadonnées';
COMMENT ON COLUMN dataset_versions.checksum IS 'Hash SHA-256 du snapshot pour détecter les changements';