# 👋 Bienvenue dans Open Data Monitoring !

Ce guide est conçu pour t'aider à démarrer sur le projet, que tu sois stagiaire, alternant ou nouveau développeur.

## 🎯 Qu'est-ce que ce projet ?

**Open Data Monitoring** agrège, surveille et historise des datasets provenant de différentes plateformes Open Data (data.gouv.fr, plateformes Huwise/Opendatasoft).

**En pratique, ça veut dire :**
- On récupère les métadonnées de datasets depuis plusieurs sources
- On suit les modifications dans le temps (snapshots quotidiens)
- On affiche tout ça dans une interface web pour que les équipes métier puissent suivre l'évolution

**Technologies principales :**
- **Backend** : Python 3.14 + FastAPI + SQLAlchemy
- **Frontend** : React + TypeScript + Vite
- **Base de données** : PostgreSQL
- **Tests** : Pytest (backend), Vitest (frontend)

## 📅 Plan d'onboarding (3 jours)

### Jour 1 : Découverte

**Objectif** : Comprendre ce qu'on fait et pourquoi

1. **Lire la documentation** (30 min)
   - [ ] README.md principal
   - [ ] Ce fichier (ONBOARDING.md)
   - [ ] ARCHITECTURE.md
   - [ ] GLOSSARY.md

2. **Explorer l'application en production/démo** (30 min)
   - Demande les accès à ton tuteur
   - Navigue dans l'interface
   - Identifie : liste des datasets, détail, historique, qualité

3. **Comprendre le flow de données** (1h)
   ```
   Plateforme externe → Adapter → Backend → Database → API → Frontend
   (data.gouv.fr)      (Python)   (FastAPI)  (Postgres)  (REST)  (React)
   ```

### Jour 2 : Setup local

**Objectif** : Faire tourner le projet sur ta machine

1. **Prérequis** (vérifier)
   ```bash
   python3 --version  # Doit être 3.14+
   node --version     # Doit être 18+
   docker --version   # Pour PostgreSQL
   ```

2. **Installation** (suivre le README)
   ```bash
   git clone <repo>
   cd open-data-monitoring

   # Backend
   python3 -m venv venv
   source venv/bin/activate
   make install

   # Base de données
   make docker-up
   # Si tu as un dump : make load

   # Frontend
   cd front && npm install
   ```

3. **Lancer l'application**
   ```bash
   # Terminal 1 : Backend
   source venv/bin/activate
   python src/run_api.py

   # Terminal 2 : Frontend
   cd front
   ./run_front.sh
   ```

4. **Vérifier que ça marche**
   - Backend : http://localhost:8000/docs (Swagger UI)
   - Frontend : http://localhost:5173
   - Si ça ne marche pas, consulte le **Troubleshooting** ci-dessous

### Jour 3 : Première contribution

**Objectif** : Faire une petite modification pour comprendre le workflow

#### Exercice guidé : Ajouter un champ dans l'interface

**Contexte** : On veut afficher la date de dernière synchro dans le tableau des datasets.

**Étapes** :

1. **Backend** : Vérifier que le champ existe
   - Le champ `last_sync_status` est déjà dans `DatasetSummary`
   - Pas besoin de modifier le backend

2. **Frontend** : Ajouter une colonne
   - Fichier : `front/src/components/DatasetTable.tsx`
   - Cherche la fonction qui rend les colonnes
   - Ajoute une nouvelle colonne pour `lastSyncStatus`

3. **Tester**
   ```bash
   cd front
   npm test -- --run
   ```

4. **Commit**
   ```bash
   git checkout -b feat/display-sync-status
   git add .
   git commit -m "feat(front): display last sync status in table"
   ```

5. **Créer une Pull Request**
   - Pousse ta branche
   - Ouvre une PR sur GitHub
   - Demande une review à ton tuteur

## 🛠️ Outils et commandes utiles

### Backend (Python)

```bash
# Activer l'environnement virtuel (TOUJOURS faire ça avant toute commande Python)
source venv/bin/activate

# Lancer les tests
pytest -v

# Lancer les tests avec couverture
pytest --cov=src --cov-report=html

# Formater le code
black .

# Linter
ruff check .

# CLI de l'application
app --help
app platform all
app dataset add <url>
```

### Frontend (TypeScript/React)

```bash
cd front

# Lancer les tests
npm test                # Mode watch
npm test -- --run       # Single run
npm run test:ui         # Interface graphique

# Lancer le dev server
npm run dev

# Build de production
npm run build

# Linter
npm run lint
```

### Base de données

```bash
# Démarrer PostgreSQL
make docker-up

# Arrêter
make docker-down

# Sauvegarder
make dump

# Restaurer
make load

# Se connecter directement à la DB
make exec-db
```

## 🔍 Où trouver quoi ?

### Backend

```
src/
├── domain/              # ⭐ Logique métier pure (modèles, règles)
│   ├── dataset/         # Tout ce qui concerne les datasets
│   ├── platform/        # Gestion des plateformes
│   └── quality/         # Évaluation qualité
├── application/         # Services applicatifs (use cases)
├── infrastructure/      # Accès aux données (DB, API externes)
│   ├── adapters/        # Code qui parle aux plateformes externes
│   ├── db/              # SQLAlchemy models
│   └── factories/       # Création d'objets complexes
└── interfaces/          # Points d'entrée (API REST, CLI)
    ├── api/             # FastAPI routes
    └── cli/             # Commandes terminal
```

### Frontend

```
front/src/
├── components/          # ⭐ Composants React réutilisables
├── pages/              # Pages de l'application
├── api/                # Client API (appels backend)
├── types/              # Types TypeScript
└── __tests__/          # Tests unitaires et intégration
```

## 🐛 Troubleshooting

### Problème : `pytest` ne trouve pas les modules

**Solution** : Tu n'as pas activé le venv !
```bash
source venv/bin/activate
pytest -v
```

### Problème : Erreur `ECONNREFUSED` lors du lancement du frontend

**Solution** : Le backend n'est pas lancé
```bash
# Terminal 1
source venv/bin/activate
python src/run_api.py
```

### Problème : Docker ne démarre pas

**Solution** : Vérifie que Docker Desktop est bien lancé
```bash
docker ps  # Doit lister les containers
```

### Problème : Tests backend échouent avec `TypeError: unsupported operand type(s) for |`

**Solution** : Mauvaise version de Python
```bash
python3 --version  # Doit être 3.10+
# Si < 3.10, utilise le venv avec la bonne version
```

### Problème : Frontend ne compile pas, erreurs de types

**Solution** : Réinstalle les dépendances
```bash
cd front
rm -rf node_modules package-lock.json
npm install
```

## 📚 Ressources pour apprendre

### Si tu débutes en...

**Python**
- [Python Official Tutorial](https://docs.python.org/3/tutorial/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

**React/TypeScript**
- [React Beta Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

**DDD (Domain-Driven Design)**
- Lire ARCHITECTURE.md d'abord
- [DDD en 10 minutes](https://medium.com/@jonathanloscalzo/domain-driven-design-principios-beneficios-y-elementos-primera-parte-aad90f30aa35)

**Git/GitHub**
- [Git Handbook](https://guides.github.com/introduction/git-handbook/)
- [Pull Request workflow](https://docs.github.com/en/pull-requests)

## 🤝 Qui contacter ?

- **Bloqué sur le setup ?** → Ton tuteur ou équipe dev
- **Question d'architecture ?** → Lead dev
- **Bug bizarre ?** → Crée une issue GitHub avec les détails

## ✅ Checklist : Tu es prêt si...

- [ ] Tu peux lancer le backend et le frontend localement
- [ ] Tu as exploré l'interface et compris les grandes features
- [ ] Tu comprends le flow de données (externe → DB → frontend)
- [ ] Tu as fait tourner les tests
- [ ] Tu as fait au moins un commit/PR de test

**Bienvenue dans l'équipe ! 🚀**
