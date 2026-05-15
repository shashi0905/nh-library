"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings are read from environment variables or .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/library"

    # Auth — must be set via environment variable (no default intentionally)
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Loans
    loan_duration_days: int = 14
    fine_rate_per_day: float = 1.00

    # Observability
    log_level: str = "INFO"


settings = Settings()
