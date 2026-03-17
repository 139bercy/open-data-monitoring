#!/bin/bash

# -----------------------------------------------------------------------------
# Script de restauration de la base locale depuis la production
# Usage: ./scripts/restore_db_from_prod.sh [SSH_HOST]
# -----------------------------------------------------------------------------

set -e

# Configuration par défaut
SSH_HOST=${1:-ds}
DB_NAME="odm"
LOCAL_DB_USER="postgres"
LOCAL_DB_PORT="5432"
DATE=$(date +"%Y-%m-%d_%H%M%S")
TEMP_DUMP="/tmp/odm_prod_${DATE}.dump"

echo "🚀 Préparation de la synchronisation de la base de données..."

# 1. Vérification de la connexion SSH
echo "🔍 Vérification de la connexion à $SSH_HOST..."
if ! ssh -q "$SSH_HOST" exit; then
    echo "❌ Erreur: Impossible de se connecter à $SSH_HOST. Vérifie ta configuration SSH."
    exit 1
fi

# 2. Dump de la base de données distante
# On utilise pg_dump avec l'option -Fc (Custom format) pour pg_restore
echo "💾 Récupération du dump depuis la production ($SSH_HOST)..."
ssh "$SSH_HOST" "pg_dump -h localhost -U postgres -d $DB_NAME -Fc" > "$TEMP_DUMP"

echo "✅ Dump récupéré : $TEMP_DUMP"

# 3. Restauration locale
echo "🔄 Restauration dans la base locale ($DB_NAME)..."

# On s'assure que la base locale existe et est propre
# Note: On utilise --clean dans pg_restore pour supprimer/recréer les objets
# S'il y a des connexions actives, pg_restore peut échouer sur le DROP.
# On peut forcer la fermeture des connexions si besoin.

pg_restore -h localhost -p "$LOCAL_DB_PORT" -U "$LOCAL_DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner --no-privileges "$TEMP_DUMP"

echo "✨ Nettoyage des fichiers temporaires..."
rm "$TEMP_DUMP"

echo "🏁 Restauration terminée avec succès !"
echo "💡 Tu peux vérifier les données avec: make exec-db"
