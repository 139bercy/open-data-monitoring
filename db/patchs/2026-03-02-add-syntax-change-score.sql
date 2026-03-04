-- Patch additionnel pour Open Data Monitoring
-- Auteur : BMad Master 🧙
-- Description : Ajout de la colonne syntax_change_score pour le pilotage des évaluations IA

ALTER TABLE dataset_quality ADD COLUMN IF NOT EXISTS syntax_change_score double precision;

COMMENT ON COLUMN dataset_quality.syntax_change_score IS 'Indice de stabilité syntaxique et structurelle (0-100) par rapport à la version précédente';
