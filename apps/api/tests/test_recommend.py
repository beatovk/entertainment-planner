import os
import json
import tempfile
import uuid
from fastapi.testclient import TestClient
import sys

# Configure temporary database before importing the app
temp_db_path = os.path.join(
    tempfile.gettempdir(), f"test_db_{uuid.uuid4().hex}.db"
)
os.environ["DB_PATH"] = temp_db_path

# Add the parent directory to the path to import the main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)


def teardown_module(module):
    if os.path.exists(temp_db_path):
        os.unlink(temp_db_path)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "db" in data
    assert "fts" in data
    assert "X-Search" in response.headers
    assert "X-Debug" in response.headers


def test_get_place_by_id():
    response = client.get("/api/places/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "name" in data


def test_recommend_places():
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


def test_recommend_places_missing_params():
    # Missing vibe
    params = {
        "intents": "tom-yum,walk",
        "lat": 13.7563,
        "lng": 100.5018,
    }
    resp = client.get("/api/places/recommend", params=params)
    assert resp.status_code == 422

    # Missing intents
    params = {
        "vibe": "lazy",
        "lat": 13.7563,
        "lng": 100.5018,
    }
    resp = client.get("/api/places/recommend", params=params)
    assert resp.status_code == 422

    # Missing coordinates
    params = {
        "vibe": "lazy",
        "intents": "tom-yum,walk",
    }
    resp = client.get("/api/places/recommend", params=params)
    assert resp.status_code == 422

