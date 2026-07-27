"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./pricewatch_dev.db"

    # JWT auth
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Telegram (optional)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # CORS: comma-separated list of exact frontend origins allowed to call
    # this API. Never "*" in production. Defaults to the Vite dev server.
    cors_origins: str = "http://localhost:5173"

    # API docs (Swagger UI / ReDoc / raw OpenAPI schema) hand an anonymous
    # internet caller a full map of every route and schema. Off by default;
    # opt in for local development with ENABLE_DOCS=1.
    enable_docs: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()
    return _settings
