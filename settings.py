from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    db_path: str = str(Path(__file__).resolve().parent / "clean.db")

    class Config:
        env_prefix = ''
        env_file = '.env'

settings = Settings()
