# open-data-monitoring - Project Context & Rules

## Core Philosophy
- **Quality Over Speed**: La propreté du code est la priorité #1. Nous ne sacrifions jamais la maintenabilité pour la vitesse de livraison.
- **Dette Technique**: Réduire la dette est un prérequis à toute nouvelle fonctionnalité.
- **Agentic Standards**: En travaillant avec des agents IA, nous exigeons une précision absolue dans les chemins de fichiers, les types et la documentation.

## Technical Rules
1. **Clean Architecture Strict**: Respecter les couches Domain -> Application -> Infrastructure.
2. **CQS Enforcement**: Chaque mutation doit passer par un UseCase/Command.
3. **Zero Fluff**: Pas de code mort, pas de placeholders.
4. **Test-First**: Chaque nouvelle règle métier doit être couverte par un test unitaire avant d'être marquée comme terminée.
5. **Type Hinting**: Utiliser les types hints pour toutes les fonctions.
6. **Documentation**: Toute nouvelle fonctionnalité doit être documentée.

## Stack
1. **Python 3.12** : Ou plus. Se lance via `source .venv/bin/activate` à partir de `open-data-monitoring`.
2. **FastAPI** :
3. **PostgreSQL**: Base de données hébergée en local. Voir `.env`
4. **Docker** : Déprécié. À ne pas retirer.
5. **Vue.js**
6. **DSFR**

## Deployment
1. **Makefile**
2. **deploy.sh**
