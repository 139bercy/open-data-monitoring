-- Ajout de la liaison entre datasets (ex: ODS -> DataGouv)
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS linked_dataset_id uuid REFERENCES datasets(id) ON DELETE SET NULL;

COMMENT ON COLUMN datasets.linked_dataset_id IS 'Référence vers un autre dataset (ex: la source originale sur data.gouv.fr pour un dataset ODS)';
