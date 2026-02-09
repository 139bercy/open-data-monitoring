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


def calculate_snapshot_diff(old: dict, new: dict) -> dict:
    """
    Calculates the differences between two snapshots (recursive).
    Returns a dict describing added, removed, and changed keys.
    """
    if not old:
        return {"all": "new_snapshot"}
        
    diff = {}
    
    all_keys = set(old.keys()) | set(new.keys())
    for key in all_keys:
        if key not in old:
            diff[key] = {"_t": "added", "new": new[key]}
        elif key not in new:
            diff[key] = {"_t": "removed", "old": old[key]}
        elif old[key] != new[key]:
            if isinstance(old[key], dict) and isinstance(new[key], dict):
                inner = calculate_snapshot_diff(old[key], new[key])
                if inner:
                    diff[key] = inner
            else:
                diff[key] = {"_t": "changed", "old": old[key], "new": new[key]}
                
    return diff
