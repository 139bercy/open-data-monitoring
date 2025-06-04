from uuid import UUID

import pytest

from application.handlers import create_platform
from application.queries.postgresql import PostgresPlatformRepository
from application.services.platform import PlatformMonitoring
from infrastructure.factories.platform import PlatformAdapterFactory


@pytest.fixture
def app(db_transaction):
    return PlatformMonitoring(
        adapter_factory=PlatformAdapterFactory,
        repository=PostgresPlatformRepository(db_transaction),
    )


platform_1 = {
    "name": "My Platform",
    "slug": "my-platform",
    "organization_id": "azertyuiop",
    "type": "test",
    "url": "https://data.mydomain.net",
    "key": "TEST_API_KEY",
}


def test_postgresql_create_platform(app, testfile):
    platform_id = create_platform(app, platform_1)
    platform = app.get(platform_id=platform_id)
    assert isinstance(platform.id, UUID)
