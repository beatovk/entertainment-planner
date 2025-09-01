from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Generator[TestClient, None, None]:
    from apps.api.app import create_app
    from apps.api.settings import Settings

    db_path = tmp_path / "test.db"
    settings = Settings(db_path=str(db_path), cache_db_path=str(tmp_path / "cache.db"))
    app = create_app(settings)
    test_client = TestClient(app)
    yield test_client


def test_recommend_with_no_candidates_returns_404(client: TestClient) -> None:
    params = {
        "city": "bangkok",
        "day": "2025-09-02",
        "vibe": "unknown_vibe",
        "intents": "zzz",
        "lat": "13.7563",
        "lng": "100.5018",
    }
    res = client.get("/api/places/recommend", params=params)
    assert res.status_code in (404, 204)

