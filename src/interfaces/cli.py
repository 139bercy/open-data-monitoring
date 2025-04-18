from pprint import pprint
from uuid import UUID

import click

from application.handlers import create_platform, sync_platform
from settings import app


@click.group()
def cli():
    """Application manager"""


@cli.group("platform")
def cli_platform():
    """Platform management"""


@cli_platform.command("create")
@click.option("-n", "--name", required=True, help="Entity name")
@click.option("-s", "--slug", required=False, help="Entity slug")
@click.option("-o", "--organization-id", required=False, help="Entity ID")
@click.option(
    "-t",
    "--type",
    required=True,
    type=click.Choice(["opendatasoft", "datagouvfr", "test"]),
)
@click.option("-u", "--url", required=True, help="Base URL")
@click.option("-k", "--key", required=False, help="API Key")
def cli_create_platform(name, slug, organization_id, type, url, key):
    """Create new platform"""
    data = {
        "name": name,
        "slug": slug,
        "organization_id": organization_id,
        "type": type,
        "url": url,
        "key": key,
    }
    platform_id = create_platform(app=app, data=data)
    pprint(platform_id)
    click.echo("Success !")


@cli_platform.command("all")
def cli_get_all_platforms():
    """Retrieve all platforms"""
    platforms = app.get_all_platforms()
    pprint(platforms)


@cli_platform.command("sync")
@click.argument("id")
def cli_sync_platform(id):
    """Sync platform and project stats"""
    platform_id = UUID(id)
    sync_platform(app, platform_id=platform_id)
    platform = app.get_platform(platform_id=platform_id)
    pprint(platform.__dict__)
