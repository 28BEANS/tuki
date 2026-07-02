"""
Tuki Backend — Application Configuration

Loads environment variables via Pydantic Settings.
All configuration is centralized here.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "Tuki API"
    app_version: str = "0.1.0"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/tuki"

    # --- Supabase ---
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""

    # --- Google Maps & Places ---
    google_maps_api_key: str = ""
    google_places_api_key: str = ""
    google_geocoding_api_key: str = ""

    # --- Google Earth Engine (future) ---
    gee_service_account: str = ""
    gee_private_key: str = ""

    # --- Auth ---
    jwt_secret: str = "changeme-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24  # 24 hours

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def async_database_url(self) -> str:
        """Ensure the database URL uses asyncpg driver."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
