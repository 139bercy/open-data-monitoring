from application.dtos.dataset import DatasetDTO
from domain.platform.ports import DatasetAdapter


class InMemoryDatasetAdapter(DatasetAdapter):
    @staticmethod
    def find_dataset_id(url):
        raise NotImplementedError

    def fetch(self, url, key, dataset_id):
        raise NotImplementedError

    @staticmethod
    def map(
        id,
        slug,
        page,
        created_at,
        last_update,
        published,
        restricted,
        download_count,
        api_calls_count,
        *args,
        **kwargs,
    ):
        dataset = DatasetDTO(
            buid=id,
            slug=slug,
            page=page,
            publisher="",
            created=created_at,
            modified=last_update,
            published=published,
            restricted=restricted,
            downloads_count=download_count,
            api_calls_count=api_calls_count,
        )
        return dataset


