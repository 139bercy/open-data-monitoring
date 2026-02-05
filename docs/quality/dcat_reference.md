# Référentiel DCAT (Data Catalog Vocabulary)

## Vue d'ensemble

DCAT est un vocabulaire RDF conçu pour faciliter l'interopérabilité entre catalogues de données publiés sur le Web. Il permet de décrire des jeux de données et des services de données de manière standardisée.

## Classes principales

### dcat:Dataset
Représente un jeu de données publié ou organisé par un seul agent.

**Propriétés obligatoires :**
- `dct:title` : Titre du dataset
- `dct:description` : Description du contenu et de l'objectif

**Propriétés recommandées :**
- `dcat:keyword` : Mots-clés décrivant le dataset
- `dct:publisher` : Entité responsable de la publication
- `dct:contactPoint` : Point de contact pour le dataset
- `dct:temporal` : Période temporelle couverte
- `dct:spatial` : Zone géographique couverte
- `dct:accrualPeriodicity` : Fréquence de mise à jour
- `dct:issued` : Date de publication
- `dct:modified` : Date de dernière modification
- `dct:license` : Licence sous laquelle le dataset est disponible

## Bonnes pratiques

### Titre (dct:title)
- **Concis** : 5 à 10 mots maximum
- **Descriptif** : Permet de comprendre immédiatement le contenu
- **Sans jargon** : Accessible au grand public
- **Exemple** : "Subventions aux associations 2023"

### Description (dct:description)
- **Complète** : 300 à 500 caractères
- **Structure** : Quoi, pourquoi, comment
- **Contexte** : Mention du producteur et de l'objectif
- **Exemple** : "Liste des subventions accordées par le Ministère aux associations en 2023. Données collectées mensuellement par la Direction des Finances. Permet de suivre la répartition budgétaire par secteur d'activité."

### Mots-clés (dcat:keyword)
- **Nombre optimal** : 3 à 7 mots-clés
- **Pertinence** : Termes recherchés par les utilisateurs
- **Variété** : Mix de termes génériques et spécifiques
- **Exemple** : ["subventions", "associations", "finances publiques", "budget"]

### Producteur (dct:publisher)
- **Format** : Nom complet de la direction/service
- **Exemple** : "Direction Générale des Finances Publiques"

### Contact (dcat:contactPoint)
- **Préférence** : Boîte aux lettres fonctionnelle (BALF)
- **Format** : Email valide
- **Exemple** : "opendata@finances.gouv.fr"

### Licence (dct:license)
- **Par défaut** : Licence Ouverte v2.0 (Etalab)
- **URI** : https://www.etalab.gouv.fr/licence-ouverte-open-licence

### Fréquence de mise à jour (dct:accrualPeriodicity)
- **Valeurs** : daily, weekly, monthly, quarterly, annual, irregular
- **Cohérence** : Doit correspondre à l'historique réel

### Couverture temporelle (dct:temporal)
- **Format** : Période définie (début/fin)
- **Exemple** : "2020-01-01/2023-12-31"

### Couverture spatiale (dct:spatial)
- **Précision** : Niveau géographique approprié
- **Exemple** : "France métropolitaine", "Région Île-de-France"

## Validation

Un dataset DCAT de qualité doit :
1. ✅ Avoir toutes les propriétés obligatoires renseignées
2. ✅ Avoir au moins 70% des propriétés recommandées
3. ✅ Respecter les formats et contraintes de chaque propriété
4. ✅ Être cohérent (dates, fréquences, etc.)
