from pprint import pprint
from uuid import UUID

import click

from application.handlers import (add_dataset, create_platform, fetch_dataset,
                                  find_dataset_id_from_url,
                                  find_platform_from_url, sync_platform)
from exceptions import DatasetHasNotChanged, WrongPlatformTypeError
from logger import logger
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
    logger.info(f"{type} - {name} - Platform created with id {platform_id}")


@cli_platform.command("all")
def cli_get_all_platforms():
    """Retrieve all platforms"""
    platforms = app.platform.get_all_platforms()
    pprint(platforms)


@cli_platform.command("sync")
@click.argument("id")
def cli_sync_platform(id):
    """Sync platform and project stats"""
    platform_id = UUID(id)
    sync_platform(app=app, platform_id=platform_id)
    result = app.platform.get(platform_id=platform_id)
    pprint(result.__dict__)


@cli.group("dataset")
def cli_platform():
    """Dataset management"""


@cli_platform.command("add")
@click.argument("url")
@click.option("-o", "--output", is_flag=True, default=False, help="Print dataset")
def cli_add_dataset(url, output):
    """Create new dataset"""
    platform = find_platform_from_url(app=app, url=url)
    dataset_id = find_dataset_id_from_url(app=app, url=url)
    dataset = fetch_dataset(platform=platform, dataset_id=dataset_id)
    if output:
        pprint(dataset)
    try:
        add_dataset(app=app, platform=platform, dataset=dataset)
    except DatasetHasNotChanged as e:
        logger.info(f"{platform.type.upper()} - {dataset_id} - {e}")
    except WrongPlatformTypeError as e:
        logger.error(f"{platform.type.upper()} - {dataset_id} - Wrong plaform error")
