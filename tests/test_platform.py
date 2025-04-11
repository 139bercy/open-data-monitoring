from uuid import UUID

import pytest

from application.commands import CreatePlatform
from application.handlers import DataMonitoring
from application.usecases import create_platform

data_eco = {
    "name": "data.economie.gouv.fr",
    "type": "opendatasoft",
    "url": "https://data.economie.gouv.fr",
    "key": "azertyuiop"
}


@pytest.fixture
def app():
    return DataMonitoring()


def test_create_platform(app: DataMonitoring):
    # Arrange & Act
    platform_id = create_platform(app, data_eco)
    # Assert
    platform = app.get_platform(platform_id=platform_id)
    assert platform.version == 1
    assert isinstance(platform.id, UUID)
