import os

os.environ["OPEN_DATA_MONITORING_ENV"] = "TEST"

import json
import uuid

import psycopg2
import pytest

from application.use_cases.create_platform import CreatePlatformCommand, CreatePlatformUseCase
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
    with open("tests/fixtures/data-eco.json") as f:
        return json.load(f)


@pytest.fixture
def datagouv_dataset():
    with open("tests/fixtures/data-gouv-dataset.json") as f:
        return json.load(f)


@pytest.fixture
def app():
    return App(uow=InMemoryUnitOfWork())


@pytest.fixture
def platform(app):
    platform = Platform(id=uuid.uuid4(), **platform_1)
    return platform


@pytest.fixture
def ods_platform(app):
    platform = Platform(id=uuid.uuid4(), **platform_1)
    platform.type = "opendatasoft"
    return platform


@pytest.fixture
def datagouv_platform(app):
    platform = Platform(id=uuid.uuid4(), **platform_1)
    platform.type = "datagouvfr"
    return platform


@pytest.fixture(scope="session")
def test_db_name(worker_id):
    return f"{TEST_DB}_{worker_id}"


@pytest.fixture(scope="session")
def setup_test_database(test_db_name):
    postgres = PostgresClient(dbname="postgres", user=TEST_USER, password=TEST_PASSWORD, host=HOST, port=PORT)
    postgres.connection.set_session(autocommit=True)
    postgres.execute(f"DROP DATABASE IF EXISTS {test_db_name} WITH (FORCE);")
    postgres.execute(f"CREATE DATABASE {test_db_name};")

    migration_conn = psycopg2.connect(
        dbname=test_db_name,
        user=TEST_USER,
        password=TEST_PASSWORD,
        host=HOST,
        port=PORT,
    )
    try:
        with migration_conn:
            with migration_conn.cursor() as cur:
                # Apply base schema
                cur.execute(open("db/init.sql").read())

                # Apply all patches in chronological order
                patch_dir = "db/patchs"
                if os.path.exists(patch_dir):
                    patches = sorted([f for f in os.listdir(patch_dir) if f.endswith(".sql")])
                    for patch in patches:
                        with open(os.path.join(patch_dir, patch)) as f:
                            cur.execute(f.read())

                # Apply base views if present
                views_file = "db/views.sql"
                if os.path.exists(views_file):
                    cur.execute(open(views_file).read())
    finally:
        postgres.close()
        migration_conn.close()

    yield test_db_name

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
            cur.execute(f"DROP DATABASE IF EXISTS {test_db_name} WITH (FORCE);")
    finally:
        conn.close()


@pytest.fixture
def db_transaction(setup_test_database):
    test_db_name = setup_test_database
    client = PostgresClient(
        dbname=test_db_name,
        user=TEST_USER,
        password=TEST_PASSWORD,
        host=HOST,
        port=int(PORT),
    )

    try:
        # TRUNCATE ALL TABLES to guarantee a fresh state per test.
        # This is strictly required because PostgresUnitOfWork calls client.commit(),
        # bypassing the mock/yield client.rollback() test strategy.
        client.execute(
            "TRUNCATE TABLE platforms, platform_sync_histories, datasets, dataset_blobs, "
            "dataset_versions, dataset_quality, users CASCADE;"
        )
        client.commit()
    except Exception as e:
        print(f"Error truncating tables: {e}")

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
    use_case = CreatePlatformUseCase(uow=pg_app.uow)
    command = CreatePlatformCommand(**platform_1)
    output = use_case.handle(command)
    platform_id = output.platform_id
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
