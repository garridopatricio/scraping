"""Navegacion y estrategias de consulta a TICA."""

from app.scraper.aereo import EstrategiaAerea
from app.scraper.base import EstrategiaModalidad, FlujoNoMigradoError
from app.scraper.dispatcher import DespachadorEstrategias, ModalidadNoDeterminadaError
from app.scraper.maritimo import EstrategiaMaritima

__all__ = [
    "DespachadorEstrategias",
    "EstrategiaAerea",
    "EstrategiaMaritima",
    "EstrategiaModalidad",
    "FlujoNoMigradoError",
    "ModalidadNoDeterminadaError",
]
