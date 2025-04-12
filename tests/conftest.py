import os

import pytest

os.environ["OPEN_DATA_MONITORING_ENV"] = "TEST"


@pytest.fixture
def testfile():
    file_path = "test.json"
    yield file_path
    if os.path.exists(file_path):
        os.remove(file_path)
