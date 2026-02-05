## Gestion des métadonnées

Les métadonnées sont des "données qui fournissent de nouvelles informations sur d'autres données". À ce titre, elles
permettent de contextualiser un jeu de données : les champs dans lesquels apparaissent des termes métier donnent des
indications sur le producteur, la fréquence des mises à jour, la licence, etc.

Le module de recherche (raccourci `Ctrl / Cmd + K`) se nourrit des métadonnées pour offrir plus de contexte aux
recherches des utilisateurs. Remplir les métadonnées permet également d'étoffer considérablement l'indexation des jeux
de données et de renforcer la pertinence du moteur de recherche.

Sur la plateforme ministérielle **data.economie.gouv.fr**, ces métadonnées, à remplir pour chaque jeu de données, se
trouvent à plusieurs endroits :

- métadonnées des champs d'un document tabulaire, qui apparaissent dans l'onglet `Traitement` du backoffice,
- métadonnées `standard`, `admin` et `DCAT` de l'onglet `Informations` du backoffice.

**Attention** : Le remplissage des métadonnées répond aux mêmes critères de concision et de clarté que ceux décrits
ci-dessus.

### Modèle de documentation

Le modèle de documentation [Datasheets for Datasets](https://arxiv.org/pdf/1803.09010) cadre la rédaction des
métadonnées en fournissant une liste de questions utiles, sur la création des jeux de données, leur composition, leur
collecte, les traitements opérés, ainsi que les modalités de diffusion ou de maintenance.

### Métadonnées requises

Les métadonnées à remplir en premier lieu sont les suivantes. Sur la plateforme, elles sont étalées sur trois catégories
qui sont autant d'onglets : _standard_, _admin_, _DCAT_.

**Métadonnées descriptives**

- **le titre** : concis, il permet aux utilisateurs de comprendre le contenu du jeu de données (5 à 10 mots),
- **la description** : brève description du contenu et de l’objectif du jeu de données (300 à 500 caractères),
- **le producteur** : indique la direction responsable de la production du jeu de données (cf. note *Point de contact*
  ci-dessous),
- **contact** : coordonnées du responsable des données ou l'adresse email fonctionnelle du bureau responsable,
- **les mots-clés** : 3 à 7 termes, (cf. encadré ci-dessous)
- **Thème** (recommandé) : catégories thématiques selon la taxonomie du portail

**Métadonnées d'administation**

- **la date de publication** : renseigne sur la temporalité des données,
- **la licence** : fixe les conditions d'utilisation et de réutilisation des données. Par défaut
  `Licence Ouverte v2.0 (Etalab)`,
- **la date de mise à jour** : elle peut être réglée automatiquement à la mise à jour des données ou des métadonnées,
- **les références** : ou tout lien vers des sources externes ou documents connexes utiles.

**Géospatiales et temporelles**

- **la fréquence de mise à jour** : renseigne sur la périodicité des mises à jour (ex : hebdomadaire, mensuelle)
- **la couverture spatiale** : détermine la zone géographique couverte par le jeu de données (ex : France entière)
- **la couverture temporelle** : détaille la période temporelle couverte par le jeu de données (ex : 2012-2023)

### Catégories et mots-clés

Les mots-clés permettent d'optimiser les recherches faites sur la plateforme ou le référencement des jeux de données sur
les moteurs de recherche en donnant des éléments de contexte supplémentaires. Les experts SEO recommandent d'ajouter aux
pages entre 1 et 5 mots-clés.

Un bon mot-clé doit être recherché par les internautes et ne doit pas être trop concurrentiel.

Déterminez le sujet principal du jeu de données, le service qu'il peut offrir, sa thématique ou encore une question qui
pourrait être facilement posée par son audience cible. Identifiez ensuite les mots-clés les plus pertinents.

Des outils comme [KeywordTool](https://keywordtool.io/fr) peuvent être utilisés pour faire les premières analyses
sémantiques.

### Point de contact

La question peut se poser de renseigner comme `email de contact` l'adresse d'une boîte à lettres fonctionnelle (BALF)
plutôt qu'un email en `finances.gouv.fr`.

Le point de contact personnel a un avantage : il permet de savoir qui est nommément responsable d’un jeu de données et
savoir précisément à qui s’adresser.

Inconvénient : il est rarement mis à jour en cas de départ et devient alors obsolète très rapidement.

Une BALF est plus anonyme mais aussi plus stable dans le temps.

Nous pouvons ici faire valoir le bon sens et laisser le choix aux producteurs de données, pourvu que :

- le point de contact renseigné soit d'une granularité adaptée,
- soit directement relié à une personne physique responsable de la production et la mise à jour des données,
- permette un traitement des demandes des utilisateurs le plus rapide et le plus efficace possible.

En cas de doute, il est recommandé de privilégier la BALF. 