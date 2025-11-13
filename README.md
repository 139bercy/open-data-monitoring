# Open Data Monitoring

## Install

### Install dependencies

Run `make install` or :

```bash
$ pip install -r requirements.txt
$ pip install -r . 
```

### Deploy database

Database is deployed with docker. Install it before on your system.

Run `make docker-up` or :

```bash
$ docker compose up --build -d
```

You can also run `make docker-down` to stop the container or :

```bash
$ docker compose down --remove-orphans -v
```

### Commandes Docker utiles (développement et tests)

- Arrêter tout et supprimer les volumes (démarrage propre) :

```bash
docker compose down -v
```

- Rebuild des images et démarrage de tous les services en arrière-plan :

```bash
docker compose up --build -d
```

- Exécuter la suite de tests dans un conteneur `backend` éphémère en ciblant le service Postgres `test` :

```bash
docker compose run --rm \
	-e ODM_TEST_USER_PASSWORD=password \
	-e ODM_TEST_DATABASE_HOST=test \
	-e ODM_TEST_DATABASE_PORT=5433 \
	backend pytest -q -r a
```

La commande ci‑dessus lance `pytest` à l'intérieur du conteneur `backend` tout en pointant sur la base `test` (pratique pour reproduire le comportement d'un CI en local).

### Load data

Before running the tasks, you need to create a platform for the domain you want to monitor :

#### Create platform

`<MY_API_KEY>` should be located in `.env` file.

```text
<MY_API_KEY>=<API_KEY>
```

```bash 
$ app platform create -n "data.example.com" -t opendatasoft -u "https://data.example.com" -k DATA_EXAMPLE_API_KEY -s 
"data-example" -o "data.example.com"                          
```

#### Add dataset

```bash
$ app dataset add https://data.example.com/explore/dataset/hello-world/
```

This are examples values, you need to replace them with your own.

Run :

```bash
$ python utils/tasks.py
```

Alternatively, you can run :

```bash
$ make load
```

This will load a file named "dump.sql" in the root of the project if it exists.

### Env

Add platforms `API_KEYS` in `.env` file :

```
$ cp .env.sample .env
```

## Usage

### CLI

```
$ app --help
```

### API

```
$ python src/run_api.py
```

### Front

```
$ ./front/run_front.sh
```

---

## Objectifs

- [x] Agréger des datasets publics de plusieurs plateformes Open Data
- [ ] Identifier les jeux de données communs sur les différentes plateformes
- [x] Historiser les changements
- [x] Fournir une interface de restitution aux métiers et aux correspondants Open Data
