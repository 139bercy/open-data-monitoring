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
