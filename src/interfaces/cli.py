import click

from application.handlers import create_platform
from settings import app


@click.group()
def cli():
    """Application adapters.cli"""


@cli.group("platform")
def cli_platform():
    """Platform management"""


@cli_platform.command("create")
@click.option("-n", "--name", required=True, help="Entity name")
@click.option("-t", "--type", required=True, type=click.Choice(["opendatasoft", "datagouvfr", "test"]))
@click.option("-u", "--url", required=True, help="Base URL")
@click.option("-k", "--key", required=False, help="API Key")
def cli_create_platform(name, type, url, key):
    data = {
        "name": name,
        "type": type,
        "url": url,
        "key": key
    }
    platform = create_platform(app=app, data=data)
    click.echo("Success !", platform)