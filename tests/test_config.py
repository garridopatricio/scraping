"""Pruebas de humo del scaffold y su configuracion."""

from pytest import MonkeyPatch

from app import __version__
from app.config import Settings, get_settings


def test_app_importa_y_expone_version() -> None:
    assert __version__ == "0.1.0"


def test_configuracion_por_defecto_respeta_limites_del_proyecto() -> None:
    settings = Settings()

    assert settings.api_prefix == "/v1"
    assert settings.query_max_days == 15
    assert settings.browser_max_retries == 3
    assert settings.cache_ttl_seconds > 0


def test_configuracion_lee_variables_con_prefijo(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TICA_BROWSER_HEADLESS", "false")
    monkeypatch.setenv("TICA_LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.browser_headless is False
    assert settings.log_level == "DEBUG"


def test_get_settings_reutiliza_instancia() -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()
