import os
import uuid
from importlib import reload

import pytest
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    db_path = tmp_path / f"{uuid.uuid4().hex}.db"
    os.environ["DB_PATH"] = str(db_path)

    from apps.api import main
    reload(main)

    monkeypatch.setattr(main.search_provider, "fts", lambda q, k: [])
    monkeypatch.setattr(main.search_provider, "knn", lambda q, k: [])

    with TestClient(main.app) as client:
        yield client

    if db_path.exists():
        db_path.unlink()


def test_recommend_with_no_candidates_returns_404(client):
    params = {
        "vibe": "any",
        "intents": "test",
        "lat": 0.0,
        "lng": 0.0,
    }
    response = client.get("/api/places/recommend", params=params)
    assert response.status_code == 404
