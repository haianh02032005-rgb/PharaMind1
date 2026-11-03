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

    # Clear the shared public trial account before issuing login tokens so
    # every visitor starts with a completely empty account.
    demo_reset_on_login: bool = True

    # Prescription uploads default to a persistent local directory for self-hosted
    # deployments. Hosted deployments should set FILE_STORAGE_BACKEND=s3 and use
    # an S3-compatible private bucket (for example, Cloudflare R2).
    file_storage_backend: str = "local"
    file_storage_local_path: str = "storage/imports"
    s3_endpoint_url: str | None = None
    s3_region: str = "auto"
    s3_bucket: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_prefix: str = "prescription-imports"

    # Local OCR for real prescription images and scanned PDFs.
    ocr_enabled: bool = True
    ocr_languages: str = "vie+eng"
    ocr_timeout_seconds: int = 45
    ocr_pdf_max_pages: int = 10
    ocr_render_dpi: int = 300
    ocr_max_image_pixels: int = 30_000_000
    ocr_tesseract_cmd: str | None = None
    ocr_tessdata_dir: str | None = None
    ocr_poppler_path: str | None = None

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
        backend = self.file_storage_backend.strip().lower()
        if backend not in {"local", "s3"}:
            raise ValueError("FILE_STORAGE_BACKEND must be either 'local' or 's3'")
        self.file_storage_backend = backend
        if backend == "s3":
            required_s3 = {
                "S3_BUCKET": self.s3_bucket,
                "S3_ACCESS_KEY_ID": self.s3_access_key_id,
                "S3_SECRET_ACCESS_KEY": self.s3_secret_access_key,
            }
            missing_s3 = [name for name, value in required_s3.items() if not value]
            if missing_s3:
                raise ValueError(
                    "S3 storage requires the following settings: " + ", ".join(missing_s3)
                )
            if not self.debug and self.s3_endpoint_url and not self.s3_endpoint_url.startswith("https://"):
                raise ValueError("S3_ENDPOINT_URL must use HTTPS when DEBUG=false")
        elif not self.file_storage_local_path.strip():
            raise ValueError("FILE_STORAGE_LOCAL_PATH cannot be empty")
        if not 5 <= self.ocr_timeout_seconds <= 300:
            raise ValueError("OCR_TIMEOUT_SECONDS must be between 5 and 300")
        if not 1 <= self.ocr_pdf_max_pages <= 50:
            raise ValueError("OCR_PDF_MAX_PAGES must be between 1 and 50")
        if not 150 <= self.ocr_render_dpi <= 600:
            raise ValueError("OCR_RENDER_DPI must be between 150 and 600")
        if not 1_000_000 <= self.ocr_max_image_pixels <= 100_000_000:
            raise ValueError("OCR_MAX_IMAGE_PIXELS must be between 1000000 and 100000000")
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
