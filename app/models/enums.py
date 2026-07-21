"""Enumeraciones compartidas por el contrato de consultas TICA."""

from enum import StrEnum


class Modalidad(StrEnum):
    """Modalidades de transporte contempladas por el proyecto."""

    AEREO = "aereo"
    MARITIMO = "maritimo"
    TERRESTRE = "terrestre"


class EstadoConsulta(StrEnum):
    """Estados normalizados que puede devolver una consulta."""

    OK = "ok"
    PENDING = "pending"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    NEEDS_REVIEW = "needs_review"
    NOT_FOUND = "not_found"
    NOT_IMPLEMENTED = "not_implemented"
