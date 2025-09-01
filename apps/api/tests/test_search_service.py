import os
import sys

# Add project root and api directory to path to import services
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, "apps", "api"))

from services.search import (
    haversine_distance,
    build_route,
    calculate_fit_score,
)


def test_haversine_distance():
    dist = haversine_distance(0, 0, 0, 1)
    assert 111000 < dist < 112500


def test_build_route_and_fit_score():
    candidates = [
        {"id": 1, "lat": 0.0, "lng": 0.0, "tags_json": ["food"], "vibe_json": {"atmosphere": "chill"}, "district": "A", "rating": 4},
        {"id": 2, "lat": 0.0, "lng": 0.005, "tags_json": ["walk"], "vibe_json": {"atmosphere": "chill"}, "district": "B", "rating": 5},
        {"id": 3, "lat": 0.0, "lng": 0.01, "tags_json": ["rooftop"], "vibe_json": {"atmosphere": "chill"}, "district": "C", "rating": 3},
        {"id": 4, "lat": 0.0, "lng": 0.02, "tags_json": ["extra"], "vibe_json": {"atmosphere": "chill"}, "district": "D", "rating": 4},
    ]
    route = build_route(candidates, 0.0, 0.0)
    assert route is not None
    assert len(route["steps"]) == 3
    score = calculate_fit_score(route, candidates, "chill", ["food"])
    assert 0.0 <= score <= 1.0
