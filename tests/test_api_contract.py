from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from interfaces.api.main import api_app

client = TestClient(api_app)


def test_get_dataset_versions_contract(monkeypatch):
    """
    Test that the versions endpoint matches frontend expectations.
    Frontend expects: { versions: [...], total_versions: number }
    """
    # 1. Arrange: Mock the repository get_versions call
    dataset_id = uuid.uuid4()
    mock_items = [{"id": str(uuid.uuid4()), "timestamp": "2024-01-01T00:00:00Z"}]
    mock_total = 1

    from settings import app as domain_app

    monkeypatch.setattr(domain_app.dataset.repository, "get_versions", MagicMock(return_value=(mock_items, mock_total)))

    # 2. Act
    response = client.get(f"/api/v1/datasets/{dataset_id}/versions")

    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert "versions" in data, f"Expected 'versions' key for frontend compatibility, got {data.keys()}"
    assert "total_versions" in data, f"Expected 'total_versions' key for frontend compatibility, got {data.keys()}"
    assert "items" not in data, "Should not use 'items' in the paginated response for versions"
