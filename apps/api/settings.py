from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "local"
    db_path: str = "./data/clean.db"
    raw_db_path: str = "./data/raw.db"
    cache_db_path: str = "./data/cache.db"
    http_timeout: int = 30
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
