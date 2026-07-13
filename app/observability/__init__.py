"""Logging y observabilidad del servicio."""

from app.observability.logging import (
    configurar_logging,
    obtener_logger,
    registrar_consulta,
    registrar_error_inesperado,
)

__all__ = [
    "configurar_logging",
    "obtener_logger",
    "registrar_consulta",
    "registrar_error_inesperado",
]
