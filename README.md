# Open Data Monitoring

## Install

Run `make install` or : 

```bash
$ pip install -r requirements.txt
$ pip install -r . 
```

Add `API_KEYS` in `.env` file : 

```text
ENV=dev
TEST_API_KEY=azertyuiop
<MY_API_KEY>=<API_KEY>
```

## Usage

```
$ app --help
```

---

## Objectifs

- Agréger des datasets publics de plusieurs plateformes Open Data
- Identifier les jeux de données communs sur les différentes plateformes
- Historiser les changements
- Fournir une interface de restitution aux métiers et aux correspondants Open Data
