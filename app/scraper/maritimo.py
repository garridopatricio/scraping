"""Adaptador de la estrategia maritima validada en la PoC."""

from playwright.async_api import Page

from app.models import ConsultaInput, Modalidad
from app.scraper.base import EstrategiaModalidad, FlujoNoMigradoError, ResultadoEstrategia
from app.scraper.domain import BusquedaConocimiento


class EstrategiaMaritima(EstrategiaModalidad):
    """Punto de extension para migrar el flujo maritimo en Sprint 3."""

    modalidad = Modalidad.MARITIMO

    async def consultar(
        self,
        page: Page,
        entrada: ConsultaInput,
        busqueda: BusquedaConocimiento,
    ) -> ResultadoEstrategia:
        raise FlujoNoMigradoError("flujo maritimo pendiente de migracion en Sprint 3")
