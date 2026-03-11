from domain.datasets.aggregate import Dataset
from domain.quality.ports import MetadataMapper


class OpendatasoftMetadataMapper(MetadataMapper):
    """Mapper for Opendatasoft datasets."""

    def map_to_llm_context(self, dataset: Dataset, raw_data: dict) -> dict:
        """Extract ODS-specific metadata."""
        return {
            "id": str(dataset.id),
            "slug": str(dataset.slug),
            "title": raw_data.get("title") or raw_data.get("dataset_id"),
            "publisher": raw_data.get("publisher"),
            "metas": {
                "default": raw_data.get("metas", {}).get("default", {}),
                "dcat": raw_data.get("metas", {}).get("dcat", {}),
            },
            "metadata": {
                "default": raw_data.get("metadata", {}).get("default", {}),
                "dcat": raw_data.get("metadata", {}).get("dcat", {}),
            },
        }


class DatagouvMetadataMapper(MetadataMapper):
    """Mapper for DataGouv datasets."""

    def map_to_llm_context(self, dataset: Dataset, raw_data: dict) -> dict:
        """Extract DataGouv-specific metadata."""
        return {
            "id": str(dataset.id),
            "slug": str(dataset.slug),
            "title": raw_data.get("title"),
            "description": raw_data.get("description"),
            "organization": raw_data.get("organization", {}).get("name") if raw_data.get("organization") else None,
            "publisher": raw_data.get("publisher"),
            "tags": raw_data.get("tags"),
            "license": raw_data.get("license"),
            "frequency": raw_data.get("frequency"),
            "created_at": raw_data.get("created_at"),
            "last_modified": raw_data.get("last_modified"),
            "metrics": raw_data.get("metrics"),
            "extras": raw_data.get("extras"),
        }
