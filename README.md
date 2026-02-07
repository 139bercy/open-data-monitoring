# Open Data Monitoring

Cette application permet d'agréger, de surveiller et d'historiser les données provenant de plusieurs plateformes Open Data.

**Objectifs :**

- **Agrégation** : centraliser les métadonnées de datasets provenant de différentes sources – notamment data.gouv.fr et les plateformes Huwise (ex-Opendatasoft).
- **Historisation** : suivre les modifications apportées aux datasets avec une granularité jour, accéder et comparer les différentes versions.
- **Restitution** : fournir une interface web de visualisation des données, destinée aux métiers et correspondants Open Data.

---

## 🛠 Prérequis

- **Python** dans sa version 3.14+
- **Node.js** pour les dépendances du frontend.
- **Docker** pour les bases de données PostgreSQL.
- **Make** qui rassemble un certain nombre de commandes utiles.

## 🚀 Installation

```bash
git clone <repository-url>
cd open-data-monitoring
python -m venv venv
source venv/bin/activate  # Sur macOS/Linux
```
```bash
make install
```

## ⚙️ Configuration

Copiez les variables d'environnement dans un fichier .env. 

```bash
cp .env.sample .env
```

Éditez le fichier `.env` pour y ajouter vos clés d'API (ex: `DATA_EXAMPLE_API_KEY`) et paramètres de connexion. 
Vous enregistrerez les références dans la base à la création d'une nouvelle plateforme. 

Les variables principales incluent :
- `DB_PASSWORD`, `DB_USER`, `DB_NAME` : pour l'accès PostgreSQL.
- `ODS_DOMAIN` : domaine Opendatasoft à surveiller.
- Clés d'API diverses pour les plateformes sources.

Le projet fonctionne en production avec une instance Huwise et une organisation data.gouv.fr. 

## 🗄 Base de données

Les commandes principales de gestion de la base de données sont rassemblées dans le Makefile. 

- **Démarrer** : `make docker-up`
- **Arrêter** : `make docker-down`
- **Initialiser (si dump présent)** : `make load` (recherche un fichier `dump.sql` à la racine)
- **Sauvegarder** : `make dump`

Sinon : 

```bash
make help
```

## ⌨️ Utilisation de la CLI

L'application expose une interface en ligne de commande appelable par `app`.

### Gestion des plateformes et datasets

Avant de monitorer des datasets, vous devez configurer une plateforme source :

```bash
# Lister les plateformes existantes
app platform all

# Créer une plateforme (opendatasoft, datagouvfr, test)
app platform create --name "Data Gouv" --type datagouvfr --url "https://www.data.gouv.fr" --organization-id "123456789"

# Ajouter un dataset à surveiller via son URL
app dataset add https://www.data.gouv.fr/fr/datasets/un-super-dataset/
```

### 🤖 Qualité Assistée par IA

Le module `quality` permet d'évaluer la qualité des métadonnées en s'appuyant sur des LLM (Large Language Models). 
Il compare les métadonnées actuelles avec des référentiels (DCAT, Charte Open Data) et suggère des améliorations.

Les référentiels sont stockés dans le dossier `src/quality/data/`.

Les adapteurs pour les différentes plateformes sont stockés dans le dossier `src/quality/adapters/`.
Seuls Ollama, Open AI et Gemini sont supportés pour le moment. 

#### Évaluer un dataset
```bash
# Évaluation rapide avec OpenAI (modèle par défaut gpt-4o-mini)
app quality evaluate <dataset_id>

# Utilisation d'un modèle local via Ollama
app quality evaluate <dataset_id> --provider ollama --model llama3.1

# Générer un rapport au format Markdown
app quality evaluate <dataset_id> --report
```

#### Options disponibles :
- `--dcat` : Chemin vers un référentiel DCAT personnalisé (Markdown).
- `--charter` : Chemin vers une charte Open Data spécifique (Markdown).
- `--output` : Format de sortie (`json` pour plus de détails, `text` pour un résumé).
- `--report` : Exporte les conclusions dans un fichier `report.md` à la racine du projet.

### Aide générale
```bash
app --help
```

## 🌐 Services

- **API** : `python src/run_api.py`
- **Interface Frontend** : `./front/run_front.sh`

## 🧪 Développement

- **Tests unitaires** : `make test`
- **Couverture de code** : `make coverage`
- **Nettoyage et formatage (Black/Isort)** : `make clean`
- **Aide Makefile** : `make help`
