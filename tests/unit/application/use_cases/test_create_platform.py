import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from application.use_cases.create_platform import CreatePlatformUseCase, CreatePlatformCommand

@pytest.fixture
def repo_mock(): return MagicMock()

@pytest.fixture
def uow_mock(): return MagicMock()

@pytest.fixture
def use_case(repo_mock, uow_mock):
    return CreatePlatformUseCase(repository=repo_mock, uow=uow_mock)

@pytest.fixture
def command():
    return CreatePlatformCommand("n", "s", "o", "opendatasoft", "https://valid.com", "k")

def test_create_success(use_case, repo_mock, command):
    # Arrange & Act
    result = use_case.handle(command)
    # Assert
    assert result.status == "success"
    repo_mock.save.assert_called_once()
