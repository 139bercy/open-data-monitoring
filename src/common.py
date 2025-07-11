import json
from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID


class JsonSerializer(json.JSONEncoder):
    """A JSON encoder which can dump UUID."""

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def get_base_url(url: str):
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    return base_url
