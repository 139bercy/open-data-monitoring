import os

os.environ["OPEN_DATA_MONITORING_ENV"] = "TEST"

import json
import uuid

import psycopg2
import pytest

from application.handlers import create_platform
from domain.platform.aggregate import Platform
from infrastructure.database.postgres import PostgresClient
from infrastructure.unit_of_work import InMemoryUnitOfWork, PostgresUnitOfWork
from settings import App
from tests.fixtures.fixtures import platform_1

TEST_DB = "odm_test"
TEST_USER = "postgres"
TEST_PASSWORD = os.environ["ODM_TEST_USER_PASSWORD"]
HOST = "localhost"
PORT = os.environ["ODM_TEST_DATABASE_PORT"]


@pytest.fixture
def testfile():
    file_path = "test.json"
    yield file_path
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def ods_dataset():
    with open("tests/fixtures/data-eco.json", "r") as f:
        return json.load(f)


@pytest.fixture
def datagouv_dataset():
    with open("tests/fixtures/data-gouv-dataset.json", "r") as f:
        return json.load(f)


@pytest.fixture
def app():
    return App(uow=InMemoryUnitOfWork())


@pytest.fixture
def platform(app):
    platform = Platform(id=uuid.uuid4(), **platform_1)
    return platform


@pytest.fixture
def ods_platform(platform):
    platform.type = "opendatasoft"
    return platform


@pytest.fixture
def datagouv_platform(platform):
    platform.type = "datagouvfr"
    return platform


@pytest.fixture()
def setup_test_database():
    postgres = PostgresClient(dbname="postgres", user=TEST_USER, password=TEST_PASSWORD, host=HOST, port=PORT)
    postgres.connection.set_session(autocommit=True)
    postgres.execute(f"DROP DATABASE IF EXISTS {TEST_DB};")
    postgres.execute(f"CREATE DATABASE {TEST_DB};")

    try:
        with (
            psycopg2.connect(
                dbname=TEST_DB,
                user=TEST_USER,
                password=TEST_PASSWORD,
                host=HOST,
                port=PORT,
            ) as migration_conn,
            migration_conn.cursor() as cur,
        ):
            cur.execute(open("db/init.sql").read())
            migration_conn.commit()
    finally:
        postgres.close()

    yield

    # Teardown
    conn = psycopg2.connect(
        dbname="postgres",
        user=TEST_USER,
        password=TEST_PASSWORD,
        host=HOST,
        port=int(PORT),
    )
    conn.set_session(autocommit=True)

    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE {TEST_DB} WITH (FORCE)")
    finally:
        conn.close()


@pytest.fixture
def db_transaction(setup_test_database):
    client = PostgresClient(
        dbname=TEST_DB,
        user=TEST_USER,
        password=TEST_PASSWORD,
        host=HOST,
        port=int(PORT),
    )
    try:
        yield client
    finally:
        client.rollback()
        client.close()


@pytest.fixture
def pg_app(db_transaction):
    uow = PostgresUnitOfWork(client=db_transaction)
    return App(uow=uow)


@pytest.fixture
def pg_platform(pg_app):
    platform_id = create_platform(pg_app, platform_1)
    platform = pg_app.platform.get(platform_id=platform_id)
    return platform


@pytest.fixture
def pg_ods_platform(pg_platform):
    pg_platform.type = "opendatasoft"
    return pg_platform


@pytest.fixture
def pg_datagouv_platform(pg_platform):
    pg_platform.type = "datagouvfr"
    return pg_platform
