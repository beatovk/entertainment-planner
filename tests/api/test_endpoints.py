import os
import uuid
from importlib import reload

import pytest
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / f"{uuid.uuid4().hex}.db"
    os.environ["DB_PATH"] = str(db_path)

    from apps.api import main
    reload(main)
    with TestClient(main.app) as client:
        yield client

    if db_path.exists():
        db_path.unlink()


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "db" in data
    assert "fts" in data
    assert "X-Search" in response.headers
    assert "X-Debug" in response.headers


def test_get_place_by_id(client):
    response = client.get("/api/places/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "name" in data


def test_recommend_places(client):
    params = {
        "vibe": "lazy",
        "intents": "tom-yum,walk,rooftop",
        "lat": 13.7563,
        "lng": 100.5018,
    }
    response = client.get("/api/places/recommend", params=params)
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert "alternatives" in data
    route = data["routes"][0]
    assert len(route["steps"]) == 3
    assert route["total_distance_m"] > 0
    assert 0 <= route["fit_score"] <= 1
    assert "X-Search" in response.headers
    assert "X-Debug" in response.headers


def test_recommend_places_missing_params(client):
    params = {
        "intents": "tom-yum,walk",
        "lat": 13.7563,
        "lng": 100.5018,
    }
    resp = client.get("/api/places/recommend", params=params)
    assert resp.status_code == 422

    params = {
        "vibe": "lazy",
        "lat": 13.7563,
        "lng": 100.5018,
    }
    resp = client.get("/api/places/recommend", params=params)
    assert resp.status_code == 422

    params = {
        "vibe": "lazy",
        "intents": "tom-yum,walk",
    }
    resp = client.get("/api/places/recommend", params=params)
    assert resp.status_code == 422
