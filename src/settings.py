import os
from pathlib import Path

from dotenv import load_dotenv

from application.services.dataset import DatasetMonitoring
from application.services.platform import PlatformMonitoring
from domain.unit_of_work import UnitOfWork
from infrastructure.database.postgres import PostgresClient
from infrastructure.unit_of_work import PostgresUnitOfWork, InMemoryUnitOfWork

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

ENV = os.environ["OPEN_DATA_MONITORING_ENV"]


class App:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.platform = PlatformMonitoring(repository=uow.platforms)
        self.dataset = DatasetMonitoring(repository=uow.datasets)


if ENV == "PROD":  # pragma: no cover
    # En production on initialise le client Postgres avec les variables
    # d'environnement. Cela évite de lever une exception et permet au
    # backend de démarrer correctement derrière un reverse-proxy (nginx).
    client = PostgresClient(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ.get("DB_HOST", "db"),
        port=int(os.environ.get("DB_PORT", 5432)),
    )
    app = App(uow=PostgresUnitOfWork(client))
elif ENV == "TEST":
    print(f"App environment = {ENV}")
    app = App(uow=InMemoryUnitOfWork())
else:  # pragma: no cover
    print(f"App environment = {ENV}")
    client = PostgresClient(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ["DB_PORT"]),
    )
    app = App(uow=PostgresUnitOfWork(client))
