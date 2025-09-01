import os
try:
    from pydantic_settings import BaseSettings  # pydantic v2
except Exception:  # pydantic may be unavailable
    class BaseSettings:  # minimal stub
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


class Settings(BaseSettings):
    app_env: str = os.getenv("APP_ENV", "local")
    db_path: str = os.getenv("DB_PATH", "./data/clean.db")
    raw_db_path: str = os.getenv("RAW_DB_PATH", "./data/raw.db")
    cache_db_path: str = os.getenv("CACHE_DB_PATH", "./data/cache.db")
    http_timeout: int = int(os.getenv("HTTP_TIMEOUT", "30"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
