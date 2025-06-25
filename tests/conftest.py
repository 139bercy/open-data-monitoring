import json
import os
import uuid

import psycopg2
import pytest

from domain.platform.aggregate import Platform
from infrastructure.adapters.in_memory import InMemoryUnitOfWork
from infrastructure.database.postgres import PostgresClient
from settings import App
from tests.fixtures.fixtures import platform_1

os.environ["OPEN_DATA_MONITORING_ENV"] = "TEST"


TEST_DB = "odm_test"
TEST_USER = "postgres"
TEST_PASSWORD = "password"
HOST = "localhost"


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


@pytest.fixture()
def setup_test_database():
    postgres = PostgresClient(
        dbname="postgres", user=TEST_USER, password=TEST_PASSWORD, host=HOST, port=5433
    )
    postgres.connection.set_session(autocommit=True)
    postgres.execute(f"DROP DATABASE IF EXISTS {TEST_DB};")
    postgres.execute(f"CREATE DATABASE {TEST_DB};")

    try:
        with psycopg2.connect(
            dbname=TEST_DB, user=TEST_USER, password=TEST_PASSWORD, host=HOST, port=5433
        ) as migration_conn, migration_conn.cursor() as cur:
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
        port=5433,
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
        port=5433,
    )
    try:
        yield client
    finally:
        client.rollback()
        client.close()
