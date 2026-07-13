"""Contrato comun para estrategias de consulta TICA."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import TYPE_CHECKING

from app.models import Modalidad

if TYPE_CHECKING:
    from playwright.async_api import Page

    from app.models import ConsultaInput
    from app.scraper.domain import BusquedaConocimiento


type ResultadoEstrategia = dict[str, object]


def fecha_para_tica(value: date) -> str:
    """Convierte la fecha ISO del contrato al formato usado por el portal."""

    return value.strftime("%d/%m/%Y")


class EstrategiaModalidad(ABC):
    """Interfaz de los adaptadores aereo y maritimo."""

    modalidad: Modalidad

    @abstractmethod
    async def consultar(
        self,
        page: Page,
        entrada: ConsultaInput,
        busqueda: BusquedaConocimiento,
    ) -> ResultadoEstrategia:
        """Ejecuta el flujo existente para la modalidad detectada."""


class FlujoNoMigradoError(RuntimeError):
    """Indica que el flujo de la PoC aun no fue migrado al modulo productivo."""
