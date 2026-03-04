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
