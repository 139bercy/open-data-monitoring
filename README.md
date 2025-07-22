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
$ app platform create -n "data.example.com" -t opendatasoft -u "https://data.example.com" -k DATA_EXAMPLE_API_KEY -s 
"data-example" -o "data.example.com"                          
```

### Add dataset

```bash
$ app dataset add https://data.example.com/explore/dataset/hello-world/
```

---

## Objectifs

- [x] Agréger des datasets publics de plusieurs plateformes Open Data
- [ ] Identifier les jeux de données communs sur les différentes plateformes
- [x] Historiser les changements
- [x] Fournir une interface de restitution aux métiers et aux correspondants Open Data
