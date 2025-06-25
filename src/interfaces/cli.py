import csv
from datetime import datetime
from pprint import pprint
from uuid import UUID

import click

from application.handlers import (upsert_dataset, create_platform, fetch_dataset,
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
        upsert_dataset(app=app, platform=platform, dataset=dataset)
    except DatasetHasNotChanged as e:
        logger.info(f"{platform.type.upper()} - {dataset_id} - {e}")
    except WrongPlatformTypeError:
        logger.error(f"{platform.type.upper()} - {dataset_id} - Wrong plaform error")


@cli.group("common")
def cli_common():
    """Various ops"""


@cli_common.command("get-publishers")
def cli_get_publishers():
    query = """
    SELECT publisher, COUNT(*) AS dataset_count
    FROM datasets
    WHERE publisher IS NOT NULL
    GROUP BY publisher
    ORDER BY publisher;
    """
    datasets = app.dataset.repository.client.fetchall(query)
    if not datasets:
        click.echo("Aucun dataset trouvé.")
        return
    filename = f"{datetime.today().strftime('%Y-%m-%d')}-publishers.csv"
    with open(filename, "w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=datasets[0].keys(), delimiter=",")
        writer.writeheader()
        writer.writerows(datasets)

    click.echo(f"-> {filename}")


@cli_platform.group("get")
def cli_get_datasets():
    """retrieve datasets"""


@cli_get_datasets.command("tests")
def cli_get_test_dataset():
    """Retrieve datasets"""
    datasets = app.dataset.repository.client.fetchall("""
    SELECT d.*
    FROM datasets d JOIN platforms p ON p.id = d.platform_id
    WHERE d.slug ILIKE '%test%' AND p.type = 'opendatasoft'
    ORDER BY timestamp DESC
    """)
    filename = f"{datetime.today().strftime('%Y-%m-%d')}-datasets-flagged-as-tests.csv"
    with open(filename, "w") as output:
        writer = csv.DictWriter(output, fieldnames=datasets[0].keys())
        writer.writeheader()
        writer.writerows(datasets)
    click.echo(f"-> {filename}")


@cli_get_datasets.command("publisher")
@click.argument("name")
def cli_get_by_publisher(name):
    """Retrieve datasets"""
    query = """
        SELECT p.name, d.timestamp, d.buid, d.slug, d.page, d.publisher,d.created, d.modified, d.published, d.restricted, d.last_sync
        FROM datasets d
        JOIN platforms p ON p.id = d.platform_id
        WHERE d.publisher ILIKE %s
        ORDER BY timestamp DESC
    """
    pattern = f"%{name}%"
    datasets = app.dataset.repository.client.fetchall(query, (pattern,))
    if not datasets:
        click.echo("Aucun dataset trouvé.")
        return

    filename = f"{datetime.today().strftime('%Y-%m-%d')}-datasets-by-publisher-{name.lower()}.csv"
    with open(filename, "w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=datasets[0].keys(), delimiter=",")
        writer.writeheader()
        writer.writerows(datasets)

    click.echo(f"-> {filename}")
