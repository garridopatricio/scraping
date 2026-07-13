"""Punto de entrada FastAPI del microservicio."""

from fastapi import FastAPI

from app import __version__
from app.api import router
from app.config import Settings, get_settings
from app.observability import configurar_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construye la aplicacion sin contener reglas de scraping."""

    active_settings = settings or get_settings()
    configurar_logging(active_settings)
    application = FastAPI(
        title=active_settings.app_name,
        version=__version__,
    )
    application.include_router(router, prefix=active_settings.api_prefix)
    return application


app = create_app()
