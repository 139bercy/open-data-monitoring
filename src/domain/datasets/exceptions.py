"""Domain exceptions for dataset bounded context."""

from typing import Union


class DatasetNotFoundError(Exception):
    """Raised when a dataset cannot be found by its identifier."""

    pass


class DatasetUnreachableError(Exception):
    """Raised when a dataset endpoint is unreachable."""

    pass


class DatasetAlreadyDeletedError(Exception):
    """Raised when attempting to delete an already deleted dataset."""

    pass


class DatasetNotDeletedError(Exception):
    """Raised when attempting to restore a non-deleted dataset."""

    pass


class InvalidMetricValueError(Exception):
    """Raised when a metric value is invalid (e.g., negative)."""

    def __init__(self, metric_name: str, value: Union[int, float]):
        self.metric_name = metric_name
        self.value = value
        super().__init__(f"Invalid value for metric '{metric_name}': {value}")
