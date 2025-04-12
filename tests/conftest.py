import json
import os

import pytest

os.environ["OPEN_DATA_MONITORING_ENV"] = "TEST"


@pytest.fixture
def testfile():
    file_path = "test.json"
    yield file_path
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def ods_dataset():
    with open("tests/fixtures/ods-dataset.json", "r") as f:
        return json.load(f)


@pytest.fixture
def datagouv_dataset():
    with open("tests/fixtures/data-gouv-dataset.json", "r") as f:
        return json.load(f)
