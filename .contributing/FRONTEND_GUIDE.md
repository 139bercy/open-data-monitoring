# 🎨 Guide Frontend - Bonnes Pratiques

Ce guide explique les conventions et bonnes pratiques spécifiques au frontend du projet.

## 📁 Structure des Fichiers

```
front/src/
├── components/          # Composants réutilisables
│   ├── DatasetTable.tsx
│   ├── DatasetDetailsModal.tsx
│   ├── Badge.tsx
│   └── ...
├── pages/              # Pages (routes)
│   ├── Home.tsx
│   ├── DatasetListPage.tsx
│   └── PlatformListPage.tsx
├── api/                # Client API
│   ├── api.ts          # Client HTTP bas niveau
│   └── datasets.ts     # Endpoints datasets
├── types/              # Types TypeScript
│   └── datasets.ts
├── __tests__/          # Tests
│   ├── components/
│   ├── api/
│   ├── setup.ts        # Configuration globale
│   └── mockData.ts     # Données de test
└── main.tsx           # Point d'entrée
```

## 🎯 Quand créer un nouveau fichier ?

### Nouveau Component

**Créer un composant SI** :
- Le code est réutilisé à plusieurs endroits
- La logique est complexe et mérite d'être isolée
- Le fichier parent dépasse 300 lignes

**Exemple** :
```tsx
// ✅ Bon : Composant réutilisable
// components/StatusBadge.tsx
export function StatusBadge({ status }: { status: string }) {
  const severity = status === "success" ? "success" : "error";
  return <Badge severity={severity}>{status}</Badge>;
}

// Utilisé dans DatasetTable, PlatformList, etc.
```

**NE PAS créer de composant pour** :
- Du JSX simple utilisé une seule fois
- Juste pour extraire 5 lignes de code

### Nouvelle Page

**Créer une page SI** :
- C'est une nouvelle route/URL
- Ça représente un écran complet de l'application

**Convention de nommage** :
```
pages/MonNouveau FichierPage.tsx   # Pour /mon-nouveau-fichier
```

### Nouveau Type

**Ajouter dans `types/datasets.ts` SI** :
- C'est un type utilisé partout dans le code
- Ça représente une entité métier (Dataset, Platform, etc.)

**Créer un nouveau fichier `types/xxx.ts` SI** :
- Les types ne concernent pas les datasets
- Le fichier `datasets.ts` devient trop gros (>200 lignes)

## 🏷️ Conventions de Nommage

### Fichiers

```
ComponentName.tsx        # PascalCase pour composants
utils.ts                 # camelCase pour utilitaires
types.ts                 # lowercase pour types/config
```

### Composants

```tsx
// PascalCase, nom descriptif
export function DatasetTable() { }        # ✅
export function Table() { }              # ❌ Trop générique
export function dataset_table() { }       # ❌ snake_case
```

### Variables et Fonctions

```tsx
// camelCase
const datasetCount = 10;              # ✅
const DatasetCount = 10;              # ❌ PascalCase réservé aux composants
const dataset_count = 10;             # ❌ snake_case (backend style)

function handleClick() { }            # ✅
function HandleClick() { }            # ❌
```

### Types et Interfaces

```tsx
// PascalCase
type DatasetSummary = { }             # ✅
type dataset_summary = { }            # ❌

interface User { }                    # ✅
interface user { }                    # ❌
```

### Constantes

```tsx
// SCREAMING_SNAKE_CASE pour vraies constantes
const MAX_PAGE_SIZE = 100;            # ✅
const API_BASE_URL = "/api/v1";       # ✅

// camelCase pour valeurs qui peuvent changer
const defaultPageSize = 25;           # ✅
```

## 🎨 Style et CSS

### Utiliser le DSFR (Design System de l'État)

Le projet utilise le Design System de l'État Français (DSFR).

**Classes disponibles** :
```tsx
// Boutons
<button className="fr-btn">Bouton</button>
<button className="fr-btn fr-btn--secondary">Secondaire</button>

// Badges
<Badge severity="success">Succès</Badge>
<Badge severity="error">Erreur</Badge>
<Badge severity="warning">Attention</Badge>

// Spacing
<div className="fr-mb-3w">Marge bottom 3 unités</div>
<div className="fr-py-4w">Padding vertical 4 unités</div>

// Typography
<p className="fr-text--sm">Petit texte</p>
<p className="fr-text--lg">Grand texte</p>
```

### Style inline : Quand et comment ?

**Utiliser style inline UNIQUEMENT pour** :
- Valeurs dynamiques (couleurs calculées, largeurs variables)
- Micro-ajustements ponctuels

```tsx
// ✅ Bon : Valeur dynamique
<div style={{ width: `${progress}%` }}>

// ✅ Bon : Flexbox rapide pour layout
<div style={{ display: "flex", gap: "0.5rem" }}>

// ❌ Éviter : Style réutilisé partout
<div style={{ color: "red", fontSize: "14px" }}>
// → Créer une classe CSS ou utiliser DSFR
```

## 📦 Gestion des Props

### Props simples

```tsx
// ✅ Bon : Destructuration claire
function Badge({ severity, children }: { severity: string; children: React.ReactNode }) {
  return <span className={`badge-${severity}`}>{children}</span>;
}

// Usage
<Badge severity="success">OK</Badge>
```

### Props complexes : Créer un type

```tsx
// ✅ Bon : Type nommé pour props complexes
type DatasetTableProps = {
  items: DatasetSummary[];
  total: number;
  page: number;
  pageSize: number;
  loading?: boolean;
  onPageChange?: (page: number) => void;
};

function DatasetTable({ items, total, page, pageSize, loading, onPageChange }: DatasetTableProps) {
  // ...
}
```

### Props optionnelles

```tsx
// Utiliser ? pour props optionnelles
type BadgeProps = {
  severity: "success" | "error" | "warning";
  children: React.ReactNode;
  small?: boolean;        # Optionnel
  noIcon?: boolean;       # Optionnel
};

// Valeurs par défaut
function Badge({ severity, children, small = false, noIcon = false }: BadgeProps) {
  // ...
}
```

## 🔄 State Management

### useState pour state local

```tsx
function DatasetList() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [loading, setLoading] = useState(false);

  // ✅ Bon : State local au composant
}
```

### useEffect pour side effects

```tsx
// ✅ Bon : Charger des données au montage
useEffect(() => {
  loadDatasets();
}, []); // Dépendances vides = 1 seule fois

// ✅ Bon : Recharger quand page change
useEffect(() => {
  loadDatasets(page);
}, [page]); // Se re-exécute si page change
```

### ⚠️ Pièges courants

```tsx
// ❌ Éviter : useEffect sans dépendances alors qu'il en a
useEffect(() => {
  console.log(datasets.length);
}, []); // datasets n'est pas dans les dépendances !

// ✅ Corriger :
useEffect(() => {
  console.log(datasets.length);
}, [datasets]);

// ❌ Éviter : Modifier le state directement
const [items, setItems] = useState([1, 2, 3]);
items.push(4);  // ❌ Mutation !

// ✅ Corriger :
setItems([...items, 4]);  // Créer nouveau tableau
```

## 🌐 Appels API

### Structure standard

```tsx
// 1. Définir les types de retour
type GetDatasetsResponse = {
  items: DatasetSummary[];
  total: number;
  page: number;
  pageSize: number;
};

// 2. Fonction API avec typage fort
export async function getDatasets(params?: {
  page?: number;
  pageSize?: number;
}): Promise<GetDatasetsResponse> {
  const response = await api.get("/v1/datasets", params);
  return transformResponse(response);  // snake_case → camelCase
}

// 3. Utilisation dans composant
function MyPage() {
  const [data, setData] = useState<GetDatasetsResponse | null>(null);

  useEffect(() => {
    getDatasets({ page: 1 }).then(setData);
  }, []);

  if (!data) return <div>Loading...</div>;
  return <DatasetTable items={data.items} />;
}
```

### Gestion des erreurs

```tsx
// ✅ Bon : Gestion explicite des erreurs
const [error, setError] = useState<string | null>(null);

try {
  const data = await getDatasets();
  setDatasets(data.items);
  setError(null);
} catch (err) {
  setError("Impossible de charger les données");
  console.error(err);
}

// Affichage conditionnel
{error && <div className="fr-alert fr-alert--error">{error}</div>}
```

## 🧪 Tests

### Fichiers de test

```
src/components/DatasetTable.tsx
src/__tests__/components/DatasetTable.test.tsx  # Même structure
```

### Structure d'un test

```tsx
import { render, screen } from "@testing-library/react";
import { DatasetTable } from "../../components/DatasetTable";
import { mockDatasets } from "../mockData";

describe("DatasetTable", () => {
  describe("Rendering", () => {
    it("should display dataset titles", () => {
      render(<DatasetTable items={mockDatasets} />);

      expect(screen.getByText("Mon Dataset")).toBeInTheDocument();
    });
  });

  describe("Empty state", () => {
    it("should show message when no items", () => {
      render(<DatasetTable items={[]} />);

      expect(screen.getByText(/Aucun/i)).toBeInTheDocument();
    });
  });
});
```

### Bonnes pratiques de test

```tsx
// ✅ Tester le comportement utilisateur
expect(screen.getByText("Mon Dataset")).toBeInTheDocument();
expect(screen.getByRole("button", { name: /Ajouter/i }));

// ❌ Éviter : Tester l'implémentation
expect(component.state.datasets.length).toBe(3);  // Fragile !

// ✅ Utiliser les queries accessibles
screen.getByRole("button");     # Meilleur
screen.getByLabelText("Email"); # Très bon
screen.getByText("Submit");     # OK

// ❌ Éviter
screen.getByClassName("btn");   # Fragile
```

## 🚫 Anti-patterns à éviter

### 1. Composants énormes

```tsx
// ❌ Éviter : 900 lignes dans un fichier
function DatasetDetailsModal() {
  // 900 lignes de code...
}

// ✅ Séparer en sous-composants
function DatasetDetailsModal() {
  return (
    <Modal>
      <InfoTab />
      <QualityTab />
      <HistoryTab />
    </Modal>
  );
}
```

### 2. Props drilling excessif

```tsx
// ❌ Éviter : Passer des props sur 5 niveaux
<App user={user}>
  <Page user={user}>
    <Section user={user}>
      <Component user={user}>
        <Button user={user} />  # Ouch !

// ✅ Utiliser un context ou state management
const UserContext = createContext();
```

### 3. Duplication de code

```tsx
// ❌ Éviter : Code copié-collé
<Badge severity={hasDesc ? "success" : "error"}>
  {hasDesc ? "Description OK" : "Manquante"}
</Badge>

<Badge severity={hasSlug ? "success" : "error"}>
  {hasSlug ? "Slug OK" : "Invalide"}
</Badge>

// ✅ Extraire en fonction
function QualityBadge({ isValid, validText, invalidText }) {
  return (
    <Badge severity={isValid ? "success" : "error"}>
      {isValid ? validText : invalidText}
    </Badge>
  );
}
```

## 📚 Ressources

### Documentation officielle
- [React Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [DSFR Documentation](https://www.systeme-de-design.gouv.fr/)

### Outils de debug
- React DevTools (extension navigateur)
- TypeScript erreurs dans VS Code
- `console.log()` stratégiquement placés

## ✅ Checklist avant de commit

- [ ] Le code compile sans erreur TypeScript
- [ ] Les tests passent (`npm test -- --run`)
- [ ] Pas de `console.log()` oubliés
- [ ] Les composants ont des noms descriptifs
- [ ] Les types sont définis pour les nouvelles fonctions
- [ ] Le code suit les conventions DSFR quand possible
- [ ] Les fichiers font moins de 300 lignes (sinon, refactorer)

---

**💡 En cas de doute, regarde le code existant et imite le style !**
