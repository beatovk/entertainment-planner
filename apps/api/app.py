from __future__ import annotations

import os
from importlib import reload

from fastapi import FastAPI

from .settings import Settings


def create_app(config: Settings) -> FastAPI:
    """Create a FastAPI app instance configured with provided settings."""
    os.environ["DB_PATH"] = config.db_path
    os.environ["CACHE_DB_PATH"] = config.cache_db_path

    from apps.api import main as main_module

    reload(main_module)
    return main_module.app


__all__ = ["create_app"]

