"""Adaptador de la estrategia aerea validada en la PoC."""

from playwright.async_api import Page

from app.models import ConsultaInput, Modalidad
from app.scraper.base import EstrategiaModalidad, FlujoNoMigradoError, ResultadoEstrategia
from app.scraper.domain import BusquedaConocimiento


class EstrategiaAerea(EstrategiaModalidad):
    """Punto de extension para migrar el flujo aereo en Sprint 2."""

    modalidad = Modalidad.AEREO

    async def consultar(
        self,
        page: Page,
        entrada: ConsultaInput,
        busqueda: BusquedaConocimiento,
    ) -> ResultadoEstrategia:
        raise FlujoNoMigradoError("flujo aereo pendiente de migracion en Sprint 2")
