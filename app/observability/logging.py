"""Configuracion y eventos estructurados de las consultas TICA."""

from __future__ import annotations

import logging
from typing import Protocol, cast

import structlog
from structlog.typing import FilteringBoundLogger

from app.config import Settings, get_settings
from app.models import ResultadoTICA


class EventLogger(Protocol):
    """Operaciones minimas del logger usadas por la aplicacion."""

    def info(self, event: str, **values: object) -> object: ...

    def exception(self, event: str, **values: object) -> object: ...


def configurar_logging(settings: Settings | None = None) -> None:
    """Configura structlog para escribir un objeto JSON por linea."""

    active_settings = settings or get_settings()
    level = getattr(logging, active_settings.log_level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def obtener_logger(name: str) -> FilteringBoundLogger:
    """Obtiene un logger JSON y aplica la configuracion por defecto si hace falta."""

    if not structlog.is_configured():
        configurar_logging()
    return cast(FilteringBoundLogger, structlog.get_logger(name))


def registrar_consulta(
    logger: EventLogger,
    *,
    resultado: ResultadoTICA,
    duracion_ms: float,
    correlacion_id: str,
    numero_busqueda: str,
) -> None:
    """Registra el resultado y el identificador consultado, sin incluir el payload."""

    tipos_por_modalidad = {
        "aereo": "guia_aerea",
        "maritimo": "bl",
        "terrestre": "dua",
    }
    modalidad = resultado.modalidad.value if resultado.modalidad else None

    logger.info(
        "consulta_tica_finalizada",
        correlacion_id=correlacion_id,
        tipo_busqueda=(
            tipos_por_modalidad.get(modalidad, "conocimiento_embarque")
            if modalidad is not None
            else "conocimiento_embarque"
        ),
        numero_busqueda=numero_busqueda,
        modalidad=modalidad,
        estado=resultado.estado.value,
        duracion_ms=round(duracion_ms, 2),
    )


def registrar_error_inesperado(
    logger: EventLogger,
    *,
    duracion_ms: float,
    correlacion_id: str,
) -> None:
    """Registra una excepcion no controlada sin exponer entrada ni credenciales."""

    logger.exception(
        "consulta_tica_error",
        correlacion_id=correlacion_id,
        modalidad=None,
        estado="unavailable",
        duracion_ms=round(duracion_ms, 2),
    )
