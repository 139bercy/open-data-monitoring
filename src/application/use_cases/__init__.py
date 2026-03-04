from typing import Protocol, TypeVar, Generic

Request = TypeVar("Request", contravariant=True)
Response = TypeVar("Response", covariant=True)

class UseCase(Protocol, Generic[Request, Response]):
    def handle(self, command: Request) -> Response:
        """Handle the input command and execute the use case logic."""
        ...
