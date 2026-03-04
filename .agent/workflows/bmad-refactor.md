---
description: Principes et processus de refactorisation (Fowler, SOLID, Tests courts)
---

Ce workflow définit les standards de refactorisation pour le projet **open-data-monitoring**.

## Principes de Refactorisation

1. **Martin Fowler (Extract Method)** :
   - Diviser les fonctions complexes en petites méthodes privées explicites.
   - Favoriser la lisibilité "en cascade" (le `handle` principal doit se lire comme un sommaire).

2. **SOLID** :
   - **SRP** : Une classe = une responsabilité.
   - **DIP** : Dépendre des abstractions (ports) et non des implémentations.

3. **Tests Unitaires (Haute Qualité)** :
   - **Contrainte strictie** : < 10 lignes par test (hors commentaires de structure).
   - **Structure** : Utiliser impérativement les marqueurs `# Arrange`, `# Act`, `# Assert`.
   - **Modularité** : Déporter la complexité du mocking dans des `fixtures` pytest.

## Processus

1. Analyser le code existant ou les tests.
2. Identifier les opportunités d'extraction (duplication, complexité cyclomatique).
3. Créer les fixtures nécessaires pour simplifier les tests.
4. Appliquer les changements et vérifier la régression avec `pytest`.
5. Mettre à jour le `walkthrough.md`.
