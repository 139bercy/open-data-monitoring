import os
from pathlib import Path

from dotenv import load_dotenv

from application.services.dataset import DatasetMonitoring
from application.services.platform import PlatformMonitoring
from domain.unit_of_work import UnitOfWork
from infrastructure.database.postgres import PostgresClient
from infrastructure.llm.openai_evaluator import OpenAIEvaluator
from infrastructure.unit_of_work import InMemoryUnitOfWork, PostgresUnitOfWork

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

ENV = os.environ["OPEN_DATA_MONITORING_ENV"]

# Security Settings
SECRET_KEY = os.environ.get("SECRET_KEY", "b3d56f7a8b9c0d1e2f3a4b5c6d7e8f9a")  # Fallback for dev only
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

# OIDC / ProConnect Settings
OIDC_AUTHORITY = os.environ.get(
    "OIDC_AUTHORITY", "https://fca.staging.numerique.gouv.fr/api/v2"
)  # Default to ProConnect Staging
OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "")
OIDC_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "")
OIDC_REDIRECT_URI = os.environ.get("OIDC_REDIRECT_URI", "http://localhost:5173/auth/callback")


class App:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.platform = PlatformMonitoring(repository=uow.platforms)
        self.dataset = DatasetMonitoring(repository=uow.datasets)
        self.evaluator = OpenAIEvaluator(model_name="gpt-4o-mini")


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
