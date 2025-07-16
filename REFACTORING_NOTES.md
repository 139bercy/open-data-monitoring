# Notes de Refactoring - Redondance dans l'initialisation de l'App

## Problème identifié

### Redondance dans la création d'instances App pour les tests

**Localisation :**
- `src/settings.py` lignes 28-29
- `tests/conftest.py` lignes 43-45

**Description :**
Il y a une duplication dans la création d'instances `App` avec `InMemoryUnitOfWork()` :

1. **Dans settings.py :**
```python
elif ENV == "TEST":
    print(f"App environment = {ENV}")
    app = App(uow=InMemoryUnitOfWork())
```

2. **Dans conftest.py :**
```python
@pytest.fixture
def app():
    return App(uow=InMemoryUnitOfWork())
```

**Conséquences :**
- Code dupliqué
- Confusion sur quelle instance utiliser
- Maintenance difficile (modifications à faire en deux endroits)
- Instance globale potentiellement problématique pour les tests

## Améliorations proposées

### Option 1 : Utiliser l'instance globale de settings.py
```python
# Dans conftest.py
@pytest.fixture
def app():
    from settings import app
    return app
```

**Avantages :** Simple, supprime la duplication
**Inconvénients :** Partage d'état global entre les tests

### Option 2 : Garder seulement la fixture et modifier settings.py
```python
# Dans settings.py - remplacer les lignes 27-29 par :
elif ENV == "TEST":
    print(f"App environment = {ENV}")
    # Pas d'instance globale pour les tests, utiliser la fixture
    app = None
```

**Avantages :** Pas d'instance globale pour les tests
**Inconvénients :** Besoin de vérifier tous les imports de `app` dans le code

### Option 3 : Créer une fonction factory (RECOMMANDÉE)
```python
# Dans settings.py
def create_app() -> App:
    if ENV == "TEST":
        return App(uow=InMemoryUnitOfWork())
    else:
        # logique pour DEV
        client = PostgresClient(...)
        return App(uow=PostgresUnitOfWork(client))

# Pour l'instance globale
app = create_app() if ENV != "TEST" else None

# Dans conftest.py
@pytest.fixture
def app():
    from settings import create_app
    return create_app()
```

**Avantages :**
- Centralise la logique de création
- Évite les instances globales pour les tests
- Facilite la maintenance
- Permet une meilleure isolation des tests

## Recommandation

**Implémenter l'Option 3** car elle :
- Résout le problème de duplication
- Améliore la structure du code
- Facilite les tests avec une meilleure isolation
- Prépare le terrain pour l'APIisation en centralisant la logique de création d'instances 