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