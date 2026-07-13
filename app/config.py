"""Configuracion tipada del microservicio."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Valores configurables mediante variables de entorno con prefijo ``TICA_``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TICA_",
        extra="ignore",
    )

    app_name: str = "Dokka TICA Scraper"
    app_env: Literal["development", "test", "production"] = "development"
    api_prefix: str = "/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    base_url: str = "https://portaltica.hacienda.go.cr/TicaExterno/"
    query_max_days: int = Field(default=15, ge=1, le=15)

    browser_headless: bool = True
    browser_timeout_ms: int = Field(default=30_000, gt=0)
    browser_max_retries: int = Field(default=3, ge=0)
    browser_backoff_seconds: float = Field(default=1.0, ge=0)

    cache_ttl_seconds: int = Field(default=3_600, gt=0)


@lru_cache
def get_settings() -> Settings:
    """Entrega una instancia compartida de configuracion."""

    return Settings()

