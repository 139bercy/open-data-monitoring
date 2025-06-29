# Open Data Monitoring

## Install

Run `make install` or :

```bash
$ pip install -r requirements.txt
$ pip install -r . 
```

### Env

Add platforms `API_KEYS` in `.env` file :

```
$ cp .env.sample .env
```

### Infrastructure

Docker commands are in the `Makefile`

## Usage

### CLI

```
$ app --help
```

### Create platform

`<MY_API_KEY>` should be located in `.env` file.

```text
<MY_API_KEY>=<API_KEY>
```

```bash 
$ app platform create -n "data.economie.gouv.fr" -t opendatasoft -u "https://data.economie.gouv.fr" -k DATA_ECO_API_KEY -s "data-economie" -o "data.economie.gouv.fr"                          
```

### Add dataset

```bash
$ app dataset add https://data.economie.gouv.fr/explore/dataset/hello-world/
```

---

## Objectifs

- [x] Agréger des datasets publics de plusieurs plateformes Open Data
- [ ] Identifier les jeux de données communs sur les différentes plateformes
- [x] Historiser les changements
- [x] Fournir une interface de restitution aux métiers et aux correspondants Open Data
