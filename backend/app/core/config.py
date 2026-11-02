from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Repository root: backend/app/core/config.py -> parents[3]
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "PharmaMind AI"
    app_version: str = "0.1.0"
    debug: bool = True
    database_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    default_timezone: str = "Asia/Bangkok"
    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "on", "debug", "dev", "development"}:
                return True
            if lowered in {"false", "0", "no", "off", "release", "prod", "production"}:
                return False
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_postgres_driver(cls, value: object) -> object:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                "DATABASE_URL is required. Set it to a PostgreSQL connection string "
                "before starting the API."
            )
        url = value.strip()
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url.removeprefix("postgres://")
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url.removeprefix("postgresql://")
        return url

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if not self.debug:
            if len(self.jwt_secret) < 32 or self.jwt_secret.lower() in {"change-me", "secret", "changeme"}:
                raise ValueError("JWT_SECRET must be a unique random value of at least 32 characters when DEBUG=false")
            if any(origin.strip() == "*" for origin in self.cors_origins):
                raise ValueError("CORS_ORIGINS cannot contain '*' when DEBUG=false")
        return self

    model_config = SettingsConfigDict(
        # Absolute path so .env is found whether commands run from the
        # repository root (uvicorn, pytest) or from backend/ (alembic).
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
