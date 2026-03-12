from unittest.mock import MagicMock

import pytest

from application.use_cases.create_platform import CreatePlatformCommand, CreatePlatformUseCase


@pytest.fixture
def repo_mock():
    return MagicMock()


@pytest.fixture
def uow_mock():
    return MagicMock()


@pytest.fixture
def use_case(uow_mock):
    return CreatePlatformUseCase(uow=uow_mock)


@pytest.fixture
def command():
    return CreatePlatformCommand("n", "s", "o", "opendatasoft", "https://valid.com", "k")


def test_create_success(use_case, uow_mock, command):
    # Arrange & Act
    result = use_case.handle(command)
    # Assert
    assert result.status == "success"
    uow_mock.platforms.save.assert_called_once()
