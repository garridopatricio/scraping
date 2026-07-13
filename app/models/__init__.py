"""Modelos de entrada, salida y dominio."""

from app.models.enums import EstadoConsulta, Modalidad
from app.models.shipment import (
    ConsultaInput,
    ContextoMaritimo,
    DatosMomento1,
    DatosMomento2,
    DatosMomento3,
    ResultadoTICA,
)

__all__ = [
    "ConsultaInput",
    "ContextoMaritimo",
    "DatosMomento1",
    "DatosMomento2",
    "DatosMomento3",
    "EstadoConsulta",
    "Modalidad",
    "ResultadoTICA",
]

