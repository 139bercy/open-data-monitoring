import os

from dotenv import load_dotenv

from application.services.dataset import DatasetMonitoring
from application.services.platform import PlatformMonitoring
from domain.unit_of_work import UnitOfWork
from infrastructure.adapters.in_memory import InMemoryUnitOfWork
from infrastructure.database.postgres import PostgresClient
from infrastructure.unit_of_work import PostgresUnitOfWork

load_dotenv(".env")

BASE_DIR = "db"
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
        port=5432,
    )
    app = App(uow=PostgresUnitOfWork(client))
