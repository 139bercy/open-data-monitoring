import os
from pathlib import Path

from dotenv import load_dotenv

from application.services.dataset import DatasetMonitoring
from application.services.platform import PlatformMonitoring
from domain.unit_of_work import UnitOfWork
from infrastructure.adapters.in_memory import InMemoryUnitOfWork
from infrastructure.database.postgres import PostgresClient
from infrastructure.unit_of_work import PostgresUnitOfWork

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
    raise NotImplementedError
elif ENV == "TEST":
    print(f"App environment = {ENV}")
    app = App(uow=InMemoryUnitOfWork())
else:  # pragma: no cover
    print(f"App environment = {ENV}")
    client = PostgresClient(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host="localhost",
        port=int(os.environ["DB_PORT"]),
    )
    app = App(uow=PostgresUnitOfWork(client))
