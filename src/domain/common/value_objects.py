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
        # Allow lowercase letters, numbers, hyphens, and underscores
        # Note: Underscores are preserved for dataset slugs (platform identifiers)
        if not re.match(r"^[a-z0-9-_]+$", self.value):
            raise InvalidDomainValueError(f"Invalid slug format: {self.value}")

    def normalize(self) -> "Slug":
        """Return normalized version of slug (lowercase, underscores to hyphens).

        WARNING: Do NOT use this for dataset slugs! Dataset slugs are unique identifiers
        from the source platform and must be preserved exactly as-is (including underscores).
        This method is intended for other use cases where slug normalization is needed.
        """
        normalized = self.value.lower().replace("_", "-")
        return Slug(normalized)

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
