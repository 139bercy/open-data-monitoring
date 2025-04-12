from click import UUID

from application.commands import CreatePlatform
from application.services import DataMonitoring


def create_platform(app: DataMonitoring, data: dict) -> UUID:
    cmd = CreatePlatform(**data)
    platform_id = app.register_platform(
        name=cmd.name, type=cmd.type, url=cmd.url, key=cmd.key
    )
    return platform_id
