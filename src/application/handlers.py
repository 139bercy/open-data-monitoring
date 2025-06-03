from uuid import uuid4

from click import UUID

from application.commands.platform import CreatePlatform, SyncPlatform
from application.services.platform import PlatformMonitoring


def create_platform(app, data: dict) -> UUID:
    cmd = CreatePlatform(**data)
    platform = app.register(
        name=cmd.name,
        slug=cmd.slug,
        organization_id=cmd.organization_id,
        type=cmd.type,
        url=cmd.url,
        key=cmd.key,
    )
    app.save(platform)
    return platform.id
