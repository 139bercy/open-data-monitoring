# 🏗️ Architecture du Projet

Ce document explique l'architecture globale du projet Open Data Monitoring.

## 📐 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    PLATEFORMES EXTERNES                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ data.gouv.fr │  │   Huwise     │  │    Autres    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
          ┌─────────────────────────────────────┐
          │     BACKEND (Python/FastAPI)        │
          │                                      │
          │  ┌─────────────────────────────┐   │
          │  │   Platform Adapters         │   │ ◄── Récupèrent les données
          │  │  (infrastructure/adapters)  │   │
          │  └──────────┬──────────────────┘   │
          │             ▼                        │
          │  ┌─────────────────────────────┐   │
          │  │   Application Layer         │   │ ◄── Use cases, orchestration
          │  │  (application/)             │   │
          │  └──────────┬──────────────────┘   │
          │             ▼                        │
          │  ┌─────────────────────────────┐   │
          │  │   Domain Layer              │   │ ◄── Logique métier
          │  │  (domain/)                  │   │
          │  └──────────┬──────────────────┘   │
          │             ▼                        │
          │  ┌─────────────────────────────┐   │
          │  │   Infrastructure/DB         │   │ ◄── Persistence
          │  │  (infrastructure/db)        │   │
          │  └──────────┬──────────────────┘   │
          └─────────────┼────────────────────────┘
                        ▼
          ┌─────────────────────────────────────┐
          │      PostgreSQL Database             │
          │  ┌────────┐  ┌────────┐  ┌────────┐│
          │  │Datasets│  │Snapshots│ │Platforms││
          │  └────────┘  └────────┘  └────────┘│
          └─────────────┬───────────────────────┘
                        │
                        ▼ (via API REST)
          ┌─────────────────────────────────────┐
          │     FRONTEND (React/TypeScript)     │
          │                                      │
          │  ┌─────────────────────────────┐   │
          │  │   Pages                     │   │ ◄── Vues principales
          │  │  (pages/)                   │   │
          │  └──────────┬──────────────────┘   │
          │             ▼                        │
          │  ┌─────────────────────────────┐   │
          │  │   Components                │   │ ◄── UI réutilisables
          │  │  (components/)              │   │
          │  └──────────┬──────────────────┘   │
          │             ▼                        │
          │  ┌─────────────────────────────┐   │
          │  │   API Client                │   │ ◄── Appels backend
          │  │  (api/)                     │   │
          │  └─────────────────────────────┘   │
          └─────────────────────────────────────┘
                        ▼
                 ┌────────────┐
                 │   USER     │
                 └────────────┘
```

## 🐍 Backend - Architecture en couches (DDD)

Le backend suit les principes du **Domain-Driven Design** avec une architecture hexagonale (ports & adapters).

### 1️⃣ Domain Layer (`src/domain/`)

**Rôle** : Contient la logique métier pure, indépendante de toute infrastructure.

**Principe** : Cette couche ne doit JAMAIS dépendre des couches inférieures (pas d'import de SQLAlchemy, FastAPI, etc.).

```
domain/
├── dataset/
│   ├── models.py          # Entités métier (Dataset, Snapshot, Version)
│   ├── ports.py           # Interfaces (Repository protocols)
│   └── services.py        # Services métier
├── platform/
│   ├── models.py          # Platform entity
│   ├── ports.py           # DatasetAdapter, PlatformRepository
│   └── services.py
└── quality/
    ├── models.py          # QualityReport
    └── service.py
```

**Exemple** :
```python
# domain/dataset/models.py
@dataclass
class Dataset:
    """Entité métier - pas de dépendance DB"""
    id: UUID
    title: str
    platform_id: UUID
    # ... logique métier pure

    def is_valid(self) -> bool:
        """Règle métier"""
        return self.title is not None and len(self.title) > 0
```

### 2️⃣ Application Layer (`src/application/`)

**Rôle** : Orchestration des use cases, coordination entre domain et infrastructure.

**Principe** : C'est ici qu'on définit les **actions utilisateur** (créer un dataset, synchroniser une plateforme, évaluer la qualité).

```
application/
├── handlers.py         # Use cases principaux
├── snapshots.py        # Gestion des snapshots
└── services/
    └── quality_assessment.py  # Service évaluation qualité
```

**Exemple** :
```python
# application/handlers.py
def sync_platform(platform_id: UUID, repo: PlatformRepository):
    """Use case: Synchroniser une plateforme"""
    platform = repo.get(platform_id)
    adapter = AdapterFactory.create(platform.type)
    datasets = adapter.fetch_datasets()
    # ... orchestration
```

### 3️⃣ Infrastructure Layer (`src/infrastructure/`)

**Rôle** : Implémentation concrète des ports (interfaces) définis dans le domain.

```
infrastructure/
├── adapters/           # Adapters pour plateformes externes
│   ├── datagouv.py    # Adapter data.gouv.fr
│   ├── opendatasoft.py # Adapter Huwise/ODS
│   └── test.py         # Adapter de test
├── db/                 # SQLAlchemy (ORM)
│   ├── models.py       # Tables DB
│   └── repositories.py # Implémentation des repos
└── factories/
    └── dataset.py      # Factory pour créer adapters
```

**Exemple** :
```python
# infrastructure/db/repositories.py
class SQLDatasetRepository(DatasetRepository):  # Implémente le port
    """Implémentation concrète avec SQLAlchemy"""
    def get(self, dataset_id: UUID) -> Dataset | None:
        db_dataset = session.query(DatasetModel).get(dataset_id)
        return self._to_domain(db_dataset)  # Convertit DB → Domain
```

### 4️⃣ Interfaces Layer (`src/interfaces/`)

**Rôle** : Points d'entrée de l'application (API REST, CLI).

```
interfaces/
├── api/                # FastAPI
│   ├── main.py         # App FastAPI
│   ├── routers/        # Routes par domaine
│   │   ├── datasets.py
│   │   ├── platforms.py
│   │   └── quality.py
│   └── schemas/        # Pydantic models (validation)
└── cli/                # Click commands
    ├── app.py
    ├── dataset.py
    ├── platform.py
    └── quality.py
```

**Exemple** :
```python
# interfaces/api/routers/datasets.py
@router.get("/datasets/{dataset_id}")
def get_dataset_detail(dataset_id: UUID):
    """Endpoint API"""
    repo = get_dataset_repository()  # Injection dépendance
    dataset = repo.get(dataset_id)
    return DatasetDetailSchema.from_domain(dataset)  # Domain → API
```

## ⚛️ Frontend - Architecture React

### Structure des fichiers

```
front/src/
├── components/          # Composants réutilisables
│   ├── DatasetTable.tsx      # Tableau de datasets
│   ├── DatasetDetailsModal.tsx  # Modal détail (933 lignes - à refactorer)
│   ├── PlatformBadge.tsx
│   └── ...
├── pages/              # Pages principales (routes)
│   ├── Home.tsx
│   ├── DatasetListPage.tsx
│   └── PlatformListPage.tsx
├── api/                # Client API
│   ├── api.ts          # Client HTTP générique
│   └── datasets.ts     # Endpoints datasets
├── types/              # Types TypeScript
│   └── datasets.ts     # DatasetSummary, DatasetDetail, etc.
└── __tests__/          # Tests
    ├── components/
    ├── api/
    └── setup.ts
```

### Flow de données Frontend

```
User Action (click)
    ↓
Event Handler (onClick)
    ↓
API Call (api/datasets.ts)
    ↓
HTTP Request → Backend
    ↓
Response (JSON)
    ↓
Data Transformation (snake_case → camelCase)
    ↓
State Update (useState/useEffect)
    ↓
Re-render Component
    ↓
UI Update
```

**Exemple** :
```typescript
// pages/DatasetListPage.tsx
const [datasets, setDatasets] = useState<DatasetSummary[]>([]);

useEffect(() => {
  // Au montage du composant
  getDatasets({ page: 1 }).then(data => {
    setDatasets(data.items);  // Met à jour le state
  });
}, []);

// Le composant se re-rend avec les nouvelles données
return <DatasetTable items={datasets} />;
```

## 🔄 Flow complet : Ajout d'un dataset

Suivons un dataset depuis l'ajout jusqu'à l'affichage :

```
1. USER: app dataset add https://data.gouv.fr/fr/datasets/mon-dataset/
   ↓
2. CLI (interfaces/cli/dataset.py)
   ↓
3. Use Case (application/handlers.py::add_dataset)
   ↓
4. Platform Adapter (infrastructure/adapters/datagouv.py)
   → Appel API data.gouv.fr
   → Récupère métadonnées
   ↓
5. Domain Model (domain/dataset/models.py::Dataset)
   → Crée entité Dataset
   ↓
6. Repository (infrastructure/db/repositories.py)
   → Sauvegarde en DB
   ↓
7. Database (PostgreSQL - table datasets)

═══════ Plus tard, dans le frontend ═══════

8. USER ouvre l'interface web
   ↓
9. Frontend (pages/DatasetListPage.tsx)
   → useEffect() au montage
   ↓
10. API Client (api/datasets.ts::getDatasets)
    → GET /api/v1/datasets
    ↓
11. Backend API (interfaces/api/routers/datasets.py)
    ↓
12. Repository (infrastructure/db/repositories.py)
    → Query en DB
    ↓
13. Response JSON
    → snake_case (DB format)
    ↓
14. Transformation (api/datasets.ts)
    → camelCase (Frontend format)
    ↓
15. Component (components/DatasetTable.tsx)
    → Affiche dans le tableau
    ↓
16. USER voit le dataset !
```

## 🔑 Concepts clés

### Snapshots & Versions

**Problème** : On veut suivre l'évolution des datasets dans le temps.

**Solution** : Système de snapshots quotidiens

```
Dataset (entité principale)
  │
  ├─ current_snapshot: SnapshotVersion
  │   ├─ downloads_count
  │   ├─ views_count
  │   └─ captured_at: 2024-02-10
  │
  └─ snapshots: List[SnapshotVersion]
      ├─ Snapshot du 2024-02-09
      ├─ Snapshot du 2024-02-08
      └─ Snapshot du 2024-02-07
```

Chaque nuit, un job crée un nouveau snapshot avec les métriques actuelles.

### Platform Adapters (Polymorphisme)

**Problème** : Chaque plateforme a sa propre API (data.gouv.fr ≠ Huwise).

**Solution** : Pattern Adapter avec interface commune

```python
# domain/platform/ports.py
class DatasetAdapter(Protocol):
    """Interface commune"""
    def fetch_datasets(self) -> List[Dataset]:
        ...

# infrastructure/adapters/datagouv.py
class DataGouvAdapter:
    """Implémentation pour data.gouv.fr"""
    def fetch_datasets(self):
        # Code spécifique data.gouv.fr
        ...

# infrastructure/adapters/opendatasoft.py
class OpendatasoftAdapter:
    """Implémentation pour Huwise"""
    def fetch_datasets(self):
        # Code spécifique Huwise
        ...
```

Le code métier manipule `DatasetAdapter` (interface) sans connaître l'implémentation.

### Injection de dépendances

**Principe** : Ne pas créer les dépendances directement, les recevoir en paramètre.

```python
# ❌ Mauvais (couplage fort)
def sync_platform(platform_id: UUID):
    repo = SQLDatasetRepository()  # Création directe
    # ...

# ✅ Bon (injection)
def sync_platform(platform_id: UUID, repo: DatasetRepository):
    # repo est injecté, peut être un fake pour les tests
    # ...
```

Avantage : Testabilité (on peut injecter un mock).

## 🧪 Tests

### Backend

```python
# tests/test_domain.py
def test_dataset_validation():
    """Test la logique métier pure"""
    dataset = Dataset(id=..., title="")
    assert not dataset.is_valid()  # Pas de DB, pas d'API
```

### Frontend

```typescript
// src/__tests__/components/DatasetTable.test.tsx
it("should display dataset titles", () => {
  render(<DatasetTable items={mockDatasets} />);
  expect(screen.getByText("Mon Dataset")).toBeInTheDocument();
});
```

Utilise **MSW** (Mock Service Worker) pour intercepter les appels API.

## 📚 Pour aller plus loin

- **DDD** : "Domain-Driven Design" par Eric Evans
- **Clean Architecture** : "Clean Architecture" par Robert C. Martin
- **Hexagonal Architecture** : [Article Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)

## ❓ Questions fréquentes

**Q : Pourquoi tant de couches ?**
R : Séparation des responsabilités. Changer de DB ou d'API ne casse pas la logique métier.

**Q : C'est pas overkill pour un petit projet ?**
R : Pour un CRUD simple, oui. Mais ici on a multiples sources de données, logique métier complexe (snapshots, qualité IA) → ça se justifie.

**Q : Quelle couche modifier pour ajouter un champ ?**
R : Ça dépend !
- DB uniquement → Infrastructure
- Logique métier → Domain
- Affichage → Frontend
- Souvent les 3 !
