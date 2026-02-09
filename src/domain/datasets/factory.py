from __future__ import annotations

from dataclasses import asdict
from typing import cast
from uuid import uuid4

from application.dtos.dataset import DatasetDTO
from domain.datasets.aggregate import Dataset
from domain.platform.aggregate import Platform
from domain.platform.ports import DatasetAdapter


class DatasetFactory:
    @staticmethod
    def create_from_adapter(adapter: DatasetAdapter, platform: Platform, raw_data: dict) -> Dataset:
        """
        Creates a Dataset aggregate from raw data using a specific adapter.
        """
        dto: DatasetDTO = cast(DatasetDTO, adapter.map(**raw_data))

        dataset = Dataset(
            id=uuid4(),
            buid=dto.buid,
            platform_id=platform.id,
            slug=dto.slug,
            title=dto.title,
            page=dto.page,
            publisher=dto.publisher,
            created=dto.created,
            modified=dto.modified,
            published=dto.published,
            restricted=dto.restricted,
            downloads_count=dto.downloads_count,
            api_calls_count=dto.api_calls_count,
            views_count=dto.views_count,
            reuses_count=dto.reuses_count,
            followers_count=dto.followers_count,
            popularity_score=dto.popularity_score,
            raw=raw_data,
        )

        if dto.quality:
            dataset.add_quality(**asdict(dto.quality))

        return dataset
