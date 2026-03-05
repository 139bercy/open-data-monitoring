-- Migration: Add users table for authentication
-- Date: 2026-03-04

CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email varchar(255) NOT NULL UNIQUE,
    hashed_password text NOT NULL,
    full_name varchar(255),
    role varchar(50) NOT NULL DEFAULT 'user',
    created_at timestamptz NOT NULL DEFAULT NOW(),
    last_login timestamptz
);

COMMENT ON TABLE users IS 'Table des utilisateurs pour l''authentification locale et SSO';

-- Create initial admin user
-- Password: admin (haché avec Argon2 via passlib par défaut)
-- Note: Dans un vrai environnement, on utiliserait un script de setup ou des variables d'env.
INSERT INTO users (email, hashed_password, full_name, role)
VALUES (
    'admin@odm.local',
    '$argon2id$v=19$m=65536,t=3,p=4$R2htba31njOGEGIMYWztfQ$/bAMysi/FgCbVRKw+MuRr8MQICPbkKB51YeJu2abjXM', -- Real hash for 'admin'
    'Administrateur ODM',
    'admin'
) ON CONFLICT (email) DO NOTHING;
