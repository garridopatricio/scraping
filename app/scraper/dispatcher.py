"""Despacho de estrategias desde la clasificacion productiva inicial."""

from collections.abc import Iterable

from playwright.async_api import Page

from app.models import ConsultaInput, Modalidad
from app.scraper.aereo import EstrategiaAerea
from app.scraper.base import EstrategiaModalidad, ResultadoEstrategia
from app.scraper.domain import BusquedaConocimiento
from app.scraper.maritimo import EstrategiaMaritima


class ModalidadNoDeterminadaError(ValueError):
    """Indica que Master no permitio clasificar el conocimiento."""


class DespachadorEstrategias:
    """Selecciona solo entre las estrategias aerea y maritima registradas."""

    def __init__(self, strategies: Iterable[EstrategiaModalidad] | None = None) -> None:
        configured = list(strategies or (EstrategiaAerea(), EstrategiaMaritima()))
        self._strategies = {strategy.modalidad: strategy for strategy in configured}

    @property
    def modalidades(self) -> frozenset[Modalidad]:
        """Modalidades que realmente forman parte del alcance actual."""

        return frozenset(self._strategies)

    def obtener(self, busqueda: BusquedaConocimiento) -> EstrategiaModalidad:
        """Obtiene la estrategia usando la modalidad ya detectada en Master."""

        try:
            modalidad = Modalidad(busqueda.modalidad_detectada)
            return self._strategies[modalidad]
        except (ValueError, KeyError) as error:
            raise ModalidadNoDeterminadaError(
                f"modalidad no soportada o no determinada: {busqueda.modalidad_detectada}"
            ) from error

    async def consultar(
        self,
        page: Page,
        entrada: ConsultaInput,
        busqueda: BusquedaConocimiento,
    ) -> ResultadoEstrategia:
        """Delega la consulta en la estrategia detectada."""

        strategy = self.obtener(busqueda)
        return await strategy.consultar(page, entrada, busqueda)
