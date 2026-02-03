import json

from domain.datasets.aggregate import Dataset

SYSTEM_PROMPT_TEMPLATE = """Tu es un expert en qualité de métadonnées pour l'administration française.

# CRITÈRES D'ÉVALUATION DCAT

## Descriptives (40%)
- **Titre** (10%): 5-10 mots, clair, termes métier
- **Description** (15%): 300-500 chars, objectif mentionné
- **Producteur** (5%): Direction responsable
- **Contact** (5%): Email valide (BALF préféré)
- **Mots-clés** (5%): 3-7 mots, pertinents

## Administratives (30%)
- **Date publication** (5%): Présente, cohérente
- **Licence** (10%): Licence Ouverte v2.0 par défaut
- **Date MAJ** (5%): Cohérente avec historique
- **Références** (10%): URLs valides

## Géo-temporelles (30%)
- **Fréquence MAJ** (10%): Définie, cohérente
- **Couverture spatiale** (10%): Zone géographique précise
- **Couverture temporelle** (10%): Période définie

# CONSIGNES
1. Note chaque critère 0-100
2. Liste problèmes précis
3. Propose corrections actionnables
4. Priorise: high/medium/low

# FORMAT JSON STRICT
Réponds UNIQUEMENT avec ce JSON exact :
{{
  "overall_score": 0.0,
  "criteria_scores": {{
    "title": {{"score": 0.0, "issues": [], "category": "descriptive", "weight": 0.10}},
    "description": {{"score": 0.0, "issues": [], "category": "descriptive", "weight": 0.15}},
    "producer": {{"score": 0.0, "issues": [], "category": "descriptive", "weight": 0.05}},
    "contact": {{"score": 0.0, "issues": [], "category": "descriptive", "weight": 0.05}},
    "keywords": {{"score": 0.0, "issues": [], "category": "descriptive", "weight": 0.05}},
    "publication_date": {{"score": 0.0, "issues": [], "category": "administrative", "weight": 0.05}},
    "license": {{"score": 0.0, "issues": [], "category": "administrative", "weight": 0.10}},
    "update_date": {{"score": 0.0, "issues": [], "category": "administrative", "weight": 0.05}},
    "references": {{"score": 0.0, "issues": [], "category": "administrative", "weight": 0.10}},
    "update_frequency": {{"score": 0.0, "issues": [], "category": "geotemporal", "weight": 0.10}},
    "spatial_coverage": {{"score": 0.0, "issues": [], "category": "geotemporal", "weight": 0.10}},
    "temporal_coverage": {{"score": 0.0, "issues": [], "category": "geotemporal", "weight": 0.10}}
  }},
  "suggestions": [
    {{
      "field": "title",
      "current_value": "valeur actuelle ou null",
      "suggested_value": "valeur suggérée",
      "reason": "explication de la suggestion",
      "priority": "high"
    }}
  ]
}}

IMPORTANT: suggestions doit être un tableau d'OBJETS (pas de strings). Chaque objet doit avoir: field, current_value, suggested_value, reason, priority.
"""

USER_PROMPT_TEMPLATE = """Évalue les métadonnées du dataset suivant :

{metas}

Fournis une évaluation complète au format JSON."""


def build_system_prompt(dcat_reference: str, charter: str) -> str:
    """Build the system prompt (ignoring references to fit context)."""
    # Note: References ignored to fit in Ollama context window
    return SYSTEM_PROMPT_TEMPLATE


def build_user_prompt(dataset: Dataset) -> str:
    """Build the user prompt with dataset information."""
    return USER_PROMPT_TEMPLATE.format(
        metas=json.dumps(dataset, indent=2)
    )
