# Scores de Santé (Health Scores) et MBIs

Les scores de santé permettent de mesurer l'utilisabilité, la fraîcheur et l'engagement des jeux de données de manière automatisée.

## Composition du Score Global

Le score global est une moyenne pondérée de trois sous-scores :
- **Qualité (50%)** : Respect des standards de métadonnées.
- **Fraîcheur (30%)** : Respect de la fréquence de mise à jour attendue.
- **Engagement (20%)** : Intensité et type d'usage.

## Calcul de l'Engagement

L'engagement est calculé sur une échelle de 0 à 100 via une formule logarithmique qui favorise l'usage qualitatif par rapport au volume brut :

$$Score = \min(100, \lfloor \ln(1+vues) \times 5 + \ln(1+appels\_api) \times 3 + \ln(1+reutilisations) \times 20 \rfloor)$$

### Pondération par Métrique
- **Réutilisations (x20)** : C'est la métrique la plus valorisée. Une réutilisation témoigne d'un projet concret basé sur la donnée.
- **Vues (x5)** : Témoigne de l'intérêt humain et de la visibilité sur les plateformes.
- **Appels API (x3)** : Mesure le volume technique. Bien que colossal sur certains jeux de données, il est moins pondéré pour éviter que les robots ne masquent le manque d'usage humain.

## Différences entre Plateformes (ODS vs DataGouv)

Il peut y avoir des écarts de score significatifs pour un même jeu de données présent sur deux plateformes :

| Métrique | Opendatasoft (ODS) | Data.gouv.fr |
| :--- | :--- | :--- |
| **Vues** | Souvent non récupérées (metrics internes) | Récupérées via l'API DataGouv |
| **Réutilisations** | Rarement déclarées sur ODS | Centralisées et nombreuses sur DataGouv |
| **Appels API** | Volume très élevé (technique) | Volume souvent "¤" (non disponible) |

### Cas d'école : Prix des carburants
- La version **DataGouv** obtient souvent un meilleur score car elle bénéficie du bonus massif des **réutilisations** (coeff x20) et des **vues** (coeff x5).
- La version **ODS** repose principalement sur les **appels API** (coeff x3). Même avec des centaines de millions d'appels, le score d'engagement est mathématiquement bridé par rapport à un jeu de données "vivant" avec des projets tiers déclarés sur DataGouv.
