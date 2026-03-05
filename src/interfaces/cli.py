import csv
import json
import os
from datetime import datetime
from pprint import pprint
from uuid import UUID

import click
import requests

from application.handlers import (
    find_dataset_id_from_url,
    find_platform_from_url,
)
from application.use_cases.create_platform import CreatePlatformCommand, CreatePlatformUseCase
from application.use_cases.sync_dataset import SyncDatasetCommand, SyncDatasetUseCase
from application.use_cases.sync_platform import SyncPlatformCommand, SyncPlatformUseCase
from domain.auth.aggregate import User
from domain.datasets.exceptions import DatasetUnreachableError
from infrastructure.security import get_password_hash
from interfaces.cli_quality import cli_quality
from logger import logger
from settings import app


@click.group()
def cli():
    """Application manager"""


# Register quality commands
cli.add_command(cli_quality)


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
    type=click.Choice(["opendatasoft", "datagouv", "test"]),
)
@click.option("-u", "--url", required=True, help="Base URL")
@click.option("-k", "--key", required=False, help="API Key")
def cli_create_platform(name, slug, organization_id, type, url, key):
    """Create new platform"""
    use_case = CreatePlatformUseCase(repository=app.platform.repository, uow=app.uow)
    command = CreatePlatformCommand(name=name, slug=slug, organization_id=organization_id, type=type, url=url, key=key)
    output = use_case.handle(command)
    logger.info(f"{type} - {name} - Platform created with id {output.platform_id}")


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
    use_case = SyncPlatformUseCase(repository=app.platform.repository, uow=app.uow)
    command = SyncPlatformCommand(platform_id=platform_id)
    use_case.handle(command)
    result = app.platform.get(platform_id=platform_id)
    pprint(result.__dict__)


@cli.group("dataset")
def cli_dataset():
    """Dataset management"""


@cli_dataset.command("add")
@click.argument("url")
@click.option("-o", "--output", is_flag=True, default=False, help="Print dataset")
def cli_add_dataset(url, output):
    """Create new dataset"""
    platform = find_platform_from_url(app=app, url=url)
    dataset_id = find_dataset_id_from_url(app=app, url=url)
    if dataset_id is None:
        logger.warning(f"Dataset not found for url: {url}")
        return
    try:
        use_case = SyncDatasetUseCase(repository=app.dataset.repository, uow=app.uow)
        command = SyncDatasetCommand(platform=platform, platform_dataset_id=dataset_id)
        output = use_case.handle(command)
        if output.status == "failed":
            logger.error(f"Failed to add dataset: {output.message}")
    except DatasetUnreachableError:
        pass


@cli_dataset.command("get")
@click.argument("dataset_id")
def cli_get_dataset(dataset_id):
    """Retrieve dataset on Opendatasoft"""
    catalog = requests.get(
        f"https://{os.environ.get('ODS_DOMAIN')}/api/explore/v2.1/catalog/datasets/{dataset_id}/",
        headers={"Authorization": f"Apikey {os.environ.get('DATA_ECO_API_KEY')}"},
    )
    pprint(catalog.json())
    with open("dataset.json", "w") as f:
        json.dump(catalog.json(), f, indent=2)


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


@cli.group("user")
def cli_user():
    """User management"""


@cli_user.command("create")
@click.option("-e", "--email", required=True, help="User email")
@click.option(
    "-p",
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="User password",
)
@click.option("-n", "--full-name", required=False, help="User full name")
@click.option("-r", "--role", required=False, default="user", help="User role")
def cli_create_user(email, password, full_name, role):
    """Create a new local user"""
    with app.uow:
        existing = app.uow.users.get_by_email(email)
        if existing:
            click.echo(f"Erreur: L'utilisateur {email} existe déjà.")
            return

        hashed_password = get_password_hash(password)
        new_user = User(email=email, hashed_password=hashed_password, full_name=full_name, role=role)
        app.uow.users.save(new_user)
        click.echo(f"Utilisateur {email} créé avec succès (ID: {new_user.id}).")


@cli_user.command("update-password")
@click.argument("email")
@click.option(
    "-p",
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="New password",
)
def cli_user_update_password(email, password):
    """Update user password"""
    with app.uow:
        user = app.uow.users.get_by_email(email)
        if not user:
            click.echo(f"Erreur: Utilisateur {email} non trouvé.")
            return

        user.hashed_password = get_password_hash(password)
        app.uow.users.save(user)
        click.echo(f"Mot de passe de {email} mis à jour avec succès.")
