import os
from datetime import datetime

import requests

from application.dtos.dataset import DatasetDTO
from domain.platform.ports import DatasetAdapter
from exceptions import DatasetUnreachableError


class OpendatasoftDatasetAdapter(DatasetAdapter):
    @staticmethod
    def find_dataset_id(url: str):
        if url.endswith("/"):
            return url.split("/")[-2]
        return url.split("/")[-1]

    def fetch(self, url: str, key: str, dataset_id: str):
        key = os.environ[key]
        automation = requests.get(
            f"{url}/api/automation/v1.0/datasets/",
            headers={"Authorization": f"Apikey {key}"},
            params={"dataset_id": dataset_id},
        )
        catalog = requests.get(
            f"{url}/api/explore/v2.1/catalog/datasets/{dataset_id}/",
            headers={"Authorization": f"Apikey {key}"},
        )
        monitoring = requests.get(
            f"{url}/api/explore/v2.1/monitoring/datasets/ods-datasets-monitoring/exports/json/?where=dataset_id: '{dataset_id}'",
            headers={"Authorization": f"Apikey {key}"},
        )
        try:
            automation_data = automation.json()
            catalog_data = catalog.json()
            monitoring_data = monitoring.json()
            data = {
                **automation_data["results"][0],
                **catalog_data,
                **monitoring_data[0],
            }
            return data
        except IndexError:
            raise DatasetUnreachableError()

    @staticmethod
    def map(*args, **kwargs) -> DatasetDTO:
        """
        map() construit un DatasetDTO à partir d'un dictionnaire ``kwargs`` provenant
        des réponses Opendatasoft (automation + catalog + monitoring). Cette
        fonction est volontairement tolérante : elle accepte plusieurs noms
        possibles pour les mêmes informations (ex. "dataset_id" ou "slug").

        Commentaires en français :
        - `kwargs` contient la fusion des réponses API ; la structure varie selon
          l'endpoint et la présence de métadonnées. On extrait les champs
          principaux en essayant plusieurs clefs possibles.
        - Les dates sont laissées telles quelles (strings ISO) : le parsing en
          datetime est fait plus haut ou dans la couche qui persiste si besoin.
        """
        # Identifiant lisible du dataset (slug)
        dataset_id = kwargs.get("dataset_id") or kwargs.get("slug") or kwargs.get("id")

        # domaine (ex: data.economie.gouv.fr) si présent
        domain = kwargs.get("domain_id") or kwargs.get("domain") or "data.economie.gouv.fr"

        # métadonnées agrégées fournies par ODS
        metadata = kwargs.get("metas") or kwargs.get("metadata") or {}

        # dates (création / modification) — essayer plusieurs emplacements
        created = (
            kwargs.get("created")
            or (metadata.get("dcat") or {}).get("created")
            or (metadata.get("default") or {}).get("data_processed")
            or None
        )
        modified = (
            kwargs.get("modified")
            or (metadata.get("default") or {}).get("modified")
            or kwargs.get("updated_at")
            or None
        )

        # Si la source ne fournit pas de date de création explicite, on
        # utilise la date de modification si disponible. Cela évite les
        # violations de contrainte NOT NULL côté base de données (la
        # colonne `created` doit toujours être renseignée). En dernier
        # recours on fournit la date/heure courante au format ISO.
        if not created:
            created = modified or datetime.utcnow().isoformat()

        # statut de publication : visibilité publique -> True
        visibility = kwargs.get("visibility") or kwargs.get("is_published")
        published = True if visibility in ("public", True, "true", "True") else False

        # restreint : valeur conservative (par défaut False)
        is_restricted = kwargs.get("is_restricted") or kwargs.get("restricted") or False

        # compteurs
        downloads_count = (
            kwargs.get("download_count")
            or kwargs.get("downloads_count")
            or kwargs.get("attachment_download_count")
            or None
        )
        api_calls_count = kwargs.get("api_call_count") or kwargs.get("api_calls_count") or None

        # éditeur/publisher
        publisher = None
        try:
            publisher = (metadata.get("default", {}) or {}).get("publisher") or (metadata.get("dcat", {}) or {}).get("publisher")
        except Exception:
            publisher = None

        # construire l'URL de la page d'information (fallback sur domain)
        page = f"https://{domain}/explore/dataset/{dataset_id}/information/" if dataset_id else None

        dataset = DatasetDTO(
            # buid doit toujours être fourni car la couche de persistence impose
            # une valeur non nulle. Si la source Opendatasoft ne fournit pas
            # d'identifiant métier stable (uid/buid), on revient sur le
            # dataset_id/slug qui est le meilleur substitut disponible.
            buid=kwargs.get("uid") or kwargs.get("buid") or dataset_id,
            slug=dataset_id,
            page=page,
            publisher=publisher,
            created=created,
            modified=modified,
            published=published,
            restricted=is_restricted,
            downloads_count=downloads_count,
            api_calls_count=api_calls_count,
        )

        return dataset
