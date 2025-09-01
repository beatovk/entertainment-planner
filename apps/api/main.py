from fastapi import FastAPI
from pathlib import Path
import os
import sys

# Make ingest and root modules importable
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from ingest.db_init import init_clean_db, seed_mock_data
from packages.search.provider import LocalSearchProvider
from middleware import TimingMiddleware
from settings import settings
from services.cache import CacheManager
from routes import router


def create_app() -> FastAPI:
    """Application factory for the Entertainment Planner API."""
    app = FastAPI(title="Entertainment Planner API")
    app.add_middleware(TimingMiddleware)

    db_file = Path(settings.db_path)
    if not db_file.exists():
        db_file.parent.mkdir(parents=True, exist_ok=True)
        init_clean_db(db_file)
        seed_mock_data(db_file)

    search_provider = LocalSearchProvider(settings.db_path)
    cache_manager = CacheManager(settings.db_path)
    app.state.search_provider = search_provider
    app.state.cache_manager = cache_manager

    # Ensure embeddings exist for kNN search
    import sqlite3

    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM embeddings")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "SELECT id, name || ' ' || IFNULL(summary_160, '') || ' ' || IFNULL(tags_json, '') FROM places"
        )
        rows = cursor.fetchall()
        conn.close()
        for doc_id, text in rows:
            search_provider.index(doc_id, text)
    else:
        conn.close()

    app.include_router(router)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
