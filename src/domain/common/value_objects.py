import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ValueObject:
    def __composite_values__(self):
        return self.__dict__.values()


class InvalidDomainValueError(Exception):
    pass


@dataclass(frozen=True)
class Slug(ValueObject):
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise InvalidDomainValueError("Slug must be a non-empty string")
        if not re.match(r"^[a-z0-9-_]+$", self.value):
            raise InvalidDomainValueError(f"Invalid slug format: {self.value}")

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class Url(ValueObject):
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise InvalidDomainValueError("URL must be a non-empty string")

        # Simple regex for URL validation
        regex = re.compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not re.match(regex, self.value):
            raise InvalidDomainValueError(f"Invalid URL format: {self.value}")

    def __str__(self):
        return self.value
