# 📖 Glossaire - Open Data Monitoring

Ce document définit les termes techniques et métier utilisés dans le projet.

## 🏢 Métier / Open Data

### Dataset (Jeu de données)
Collection de données publiée sur une plateforme open data. Contient des métadonnées (titre, description, organisation) et des ressources (fichiers CSV, JSON, etc.).

**Exemple** : "Base Sirene des entreprises" sur data.gouv.fr

### Platform (Plateforme)
Site web qui héberge et diffuse des datasets open data.

**Exemples** :
- data.gouv.fr (national français)
- data.economie.gouv.fr (Huwise)
- data.grandlyon.com (Opendatasoft)

### Publisher / Producteur
Organisation qui publie un dataset (ministère, collectivité, entreprise publique).

**Exemple** : "INSEE" pour la base Sirene

### Resource (Ressource)
Fichier téléchargeable attaché à un dataset (CSV, JSON, PDF, etc.).

### Metadata (Métadonnées)
Informations qui décrivent un dataset : titre, description, licence, fréquence de mise à jour, etc.

### DCAT (Data Catalog Vocabulary)
Standard W3C pour décrire des catalogues de données. Définit comment structurer les métadonnées.

### Open Data
Données publiques librement accessibles et réutilisables, souvent sous licence ouverte.

## 🔧 Technique - Backend

### Snapshot (Instantané)
Photo des métadonnées et métriques d'un dataset à un instant T. Permet de suivre l'évolution dans le temps.

**Exemple** :
```
Snapshot du 2024-02-10:
  - downloads_count: 1000
  - views_count: 5000

Snapshot du 2024-02-09:
  - downloads_count: 950
  - views_count: 4800
```

### SnapshotVersion
Représentation d'un snapshot avec toutes ses données (metrics + metadata).

### BUID (Business Unique ID)
Identifiant du dataset sur la plateforme source. Utilisé pour matcher les datasets lors de la synchro.

**Exemple** :
- data.gouv.fr → `"53698f4fa3a729239d2036df"`
- Opendatasoft → `"base-sirene"`

### Slug
Version URL-friendly du titre d'un dataset. Sans accents, espaces remplacés par des traits d'union.

**Exemple** : "Base SIRENE des entreprises" → `"base-sirene-des-entreprises"`

### Adapter (Adaptateur)
Code qui se connecte à une plateforme externe pour récupérer des données. Implémente une interface commune.

**Types d'adapters** :
- `DataGouvAdapter` : Pour data.gouv.fr
- `OpendatasoftAdapter` : Pour plateformes Huwise/ODS
- `TestAdapter` : Pour les tests

### Repository (Dépôt)
Couche d'accès aux données. Abstrait la base de données du reste du code.

**Interface** : `DatasetRepository` (protocol)
**Implémentation** : `SQLDatasetRepository` (SQLAlchemy)

### Domain Model (Modèle métier)
Représentation Python d'une entité métier (Dataset, Platform, etc.), indépendante de la DB.

### Entity (Entité)
Objet avec une identité unique (UUID). Exemples : Dataset, Platform, Snapshot.

### Value Object
Objet défini par ses attributs, sans identité propre. Exemple : URL, Date, Score.

## 🏗️ Architectur

e / DDD

### DDD (Domain-Driven Design)
Approche de conception logicielle qui place la logique métier au centre. Le code reflète le langage métier.

### Hexagonal Architecture / Ports & Adapters
Architecture où le domain (métier) est au centre, entouré de ports (interfaces) et adapters (implémentations).

```
[Platform API] → [Adapter] → [Port] → [Domain]
                                      ↓
                                    [Port] → [Repository] → [Database]
```

### Domain Layer (Couche métier)
Contient la logique métier pure. Pas de dépendance à la DB, API, framework.

### Application Layer (Couche application)
Orchestration des use cases. Coordonne domain et infrastructure.

### Infrastructure Layer (Couche infrastructure)
Implémentation technique : DB, API externes, fichiers, etc.

### Port (Interface)
Contrat définissant ce qu'un composant doit faire, sans dire comment.

**Exemple** : `DatasetRepository` (protocol Python)

### Use Case (Cas d'usage)
Action métier qu'un utilisateur peut effectuer.

**Exemples** :
- Ajouter un dataset à surveiller
- Synchroniser une plateforme
- Évaluer la qualité d'un dataset

### Dependency Injection (Injection de dépendances)
Pattern où les dépendances sont passées en paramètre au lieu d'être créées directement.

**Avantage** : Testabilité, flexibilité

## ⚛️ Frontend

### Component (Composant)
Bloc réutilisable de l'interface React.

**Exemples** :
- `DatasetTable` : Tableau de datasets
- `Badge` : Pastille de couleur avec texte

### Page
Composant représentant une route de l'application.

**Exemples** :
- `Home` : Page d'accueil
- `DatasetListPage` : Liste des datasets

### Props (Propriétés)
Données passées à un composant React depuis son parent.

```tsx
<Badge severity="success">Validé</Badge>
         ^^^^^^^^^^^^^^^^  ^^^^^^
           prop name      prop value
```

### State (État)
Données gérées par un composant qui peuvent changer et déclencher un re-render.

```tsx
const [datasets, setDatasets] = useState<Dataset[]>([]);
```

### Hook
Fonction React qui permet d'utiliser des features (state, effects, etc.).

**Exemple** : `useState`, `useEffect`, `useMemo`

### API Client
Code qui fait des requêtes HTTP au backend.

**Exemple** : `api/datasets.ts`

### Type (TypeScript)
Définition de la structure d'un objet en TypeScript.

```typescript
type Dataset = {
  id: string;
  title: string;
  ...
};
```

### Snake Case vs Camel Case
Deux conventions de nommage :
- **snake_case** : `downloads_count` (backend Python, DB)
- **camelCase** : `downloadsCount` (frontend TypeScript)

Le frontend transforme automatiquement snake → camel.

## 🧪 Tests

### Unit Test (Test unitaire)
Test d'une petite partie du code de manière isolée.

**Exemple** : Tester qu'un dataset vide n'est pas valide

### Integration Test (Test d'intégration)
Test de plusieurs composants ensemble.

**Exemple** : Tester qu'une page appelle l'API et affiche les données

### Mock (Simulacre)
Fausse implémentation utilisée dans les tests.

**Exemple** : Fake repository qui retourne des données en dur

### MSW (Mock Service Worker)
Bibliothèque qui intercepte les requêtes HTTP dans les tests frontend.

### Characterization Test
Test qui documente le comportement actuel du code, même s'il n'est pas idéal.

**Principe Feathers** : "Je ne sais pas ce que ce code devrait faire, mais je sais ce qu'il fait actuellement. Je le teste."

## 🛠️ Outils

### FastAPI
Framework web Python moderne pour créer des APIs REST.

### SQLAlchemy
ORM (Object-Relational Mapping) Python pour interagir avec la base de données.

### Pydantic
Bibliothèque Python de validation de données avec types.

### React
Bibliothèque JavaScript pour construire des interfaces utilisateurs.

### TypeScript
Sur-ensemble de JavaScript avec typage statique.

### Vite
Build tool moderne pour applications web (plus rapide que Webpack).

### Vitest
Framework de test pour JavaScript/TypeScript, compatible avec Vite.

### PostgreSQL
Base de données relationnelle open source.

### Docker
Outil pour containeriser des applications (ici, sert pour PostgreSQL).

## 📊 Métriques

### Downloads Count (Nombre de téléchargements)
Combien de fois les ressources d'un dataset ont été téléchargées.

### Views Count (Nombre de vues)
Combien de fois la page du dataset a été consultée.

### Reuses Count (Nombre de réutilisations)
Combien de projets/applications réutilisent ce dataset (sur data.gouv.fr).

### Followers Count (Nombre d'abonnés)
Combien d'utilisateurs suivent ce dataset.

### Popularity Score (Score de popularité)
Métrique calculée combinant vues, téléchargements, réutilisations.

## 🤖 Qualité / IA

### LLM (Large Language Model)
Modèle d'IA de type GPT capable d'analyser du texte.

**Utilisé pour** : Évaluer la qualité des métadonnées

### Quality Indicator (Indicateur de qualité)
Métrique binaire de qualité d'un dataset.

**Exemples** :
- `has_description` : A-t-il une description ?
- `is_slug_valid` : Le slug est-il valide (pas de caractères spéciaux) ?

### Evaluation (Évaluation)
Analyse par IA des métadonnées d'un dataset pour suggérer des améliorations.

## ⚙️ Configuration

### Environment Variable (Variable d'environnement)
Configuration stockée dans `.env`, pas dans le code.

**Exemples** :
- `DB_PASSWORD` : Mot de passe base de données
- `OPENAI_API_KEY` : Clé API OpenAI

### Virtual Environment / venv
Environnement Python isolé pour éviter les conflits de dépendances.

**Commande** : `source venv/bin/activate`

## 🔗 Abréviations courantes

- **API** : Application Programming Interface
- **CLI** : Command Line Interface
- **DB** : Database
- **DTO** : Data Transfer Object
- **FK** : Foreign Key (clé étrangère)
- **HTTP** : HyperText Transfer Protocol
- **JSON** : JavaScript Object Notation
- **ORM** : Object-Relational Mapping
- **REST** : Representational State Transfer
- **CRUD** : Create, Read, Update, Delete
- **UUID** : Universally Unique Identifier

---

**💡 Astuce** : Si tu vois un terme que tu ne comprends pas, cherche-le ici en premier !
