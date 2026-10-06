from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    API_ENV: str = "production"
    LOG_LEVEL: str = "INFO"
    SERVICE_NAME: str = "freight-rate-predictor"
    VERSION: str = "1.0.0"

    MODEL_ARTIFACT_PATH: Path = BASE_DIR / "artifacts" / "freight_rate_model.joblib"
    MAX_BATCH_SIZE: int = 1000
    CORS_ORIGINS: List[str] = ["*"]
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./freight_app.db"
    TEST_DATABASE_URL: Union[str, None] = None
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
