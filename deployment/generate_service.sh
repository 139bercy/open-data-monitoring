#!/bin/bash

# Configuration par défaut
APP_PATH=$(pwd)

# Aide
usage() {
    echo "Usage: $0 [-p path]"
    echo "  -p : Chemin absolu vers l'application (Défaut: $APP_PATH)"
    exit 1
}

# Parsing des options
while getopts "p:h" opt; do
    case $opt in
        p) APP_PATH=$OPTARG ;;
        h) usage ;;
        *) usage ;;
    esac
done

TEMPLATE="deployment/odm-api.service.template"
OUTPUT="deployment/odm-api.service"

# Remplacement des placeholders via Bash pur (Zéro dépendance externe)
# On lit le fichier via redirection (<) pour éviter l'usage de 'cat'
template_content=$(<"$TEMPLATE")
expanded_content="${template_content//\{\{APP_PATH\}\}/$APP_PATH}"
echo "$expanded_content" > "$OUTPUT"

echo "✅ Fichier généré : $OUTPUT"
echo "👉 Assurez-vous que le dossier logs existe : mkdir -p $APP_PATH/logs"
echo "👉 Installation (User Service) :"
echo "   mkdir -p ~/.config/systemd/user/"
echo "   cp $OUTPUT ~/.config/systemd/user/"
echo "   systemctl --user daemon-reload"
echo "   systemctl --user enable --now odm-api"
echo "   (Optionnel) Activer le mode persistant : loginctl enable-linger \$(whoami)"
