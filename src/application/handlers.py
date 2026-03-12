from common import get_base_url
from domain.platform.aggregate import Platform
from infrastructure.factories.dataset import DatasetAdapterFactory
from settings import App


def find_platform_from_url(app: App, url: str) -> Platform | None:
    """Identify the platform associated with a given dataset URL based on its domain."""
    with app.uow:
        try:
            return app.platform.repository.get_by_domain(get_base_url(url))
        except ValueError:
            return None


def find_dataset_id_from_url(app: App, url: str) -> str | None:
    """Extract a platform-specific dataset ID from a full source URL."""
    platform = find_platform_from_url(app=app, url=url)
    if platform is None:
        return None
    factory = DatasetAdapterFactory()
    adapter = factory.create(platform_type=platform.type)
    return adapter.find_dataset_id(url=url)
