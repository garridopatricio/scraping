"""Pruebas de ramas de estado del orquestador."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from typing import cast

import pytest
from playwright.async_api import Page

from app.cache import InMemoryResultCache
from app.config import Settings
from app.models import ConsultaInput, EstadoConsulta, Modalidad, ResultadoTICA
from app.orchestrator.consulta import ConsultaOrchestrator
from app.scraper.base import FlujoNoMigradoError, ResultadoEstrategia
from app.scraper.browser import BrowserUnavailableError
from app.scraper.captcha import CaptchaRequiredError
from app.scraper.domain import BusquedaConocimiento


class FakeBrowser:
    def __init__(
        self,
        *,
        start_error: Exception | None = None,
        captcha: bool = False,
    ) -> None:
        self.start_error = start_error
        self.captcha = captcha
        self.page = cast(Page, object())

    @asynccontextmanager
    async def pagina(self) -> AsyncIterator[Page]:
        if self.start_error:
            raise self.start_error
        yield self.page

    async def asegurar_sin_captcha(self, page: Page) -> None:
        assert page is self.page
        if self.captcha:
            raise CaptchaRequiredError("captcha")


class FakeDispatcher:
    def __init__(self, result: ResultadoEstrategia) -> None:
        self.result = result
        self.calls = 0

    async def consultar(
        self,
        page: Page,
        entrada: ConsultaInput,
        busqueda: BusquedaConocimiento,
    ) -> ResultadoEstrategia:
        self.calls += 1
        return self.result


class PendingMigrationDispatcher:
    async def consultar(
        self,
        page: Page,
        entrada: ConsultaInput,
        busqueda: BusquedaConocimiento,
    ) -> ResultadoEstrategia:
        raise FlujoNoMigradoError("flujo pendiente")


class FakeLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def info(self, event: str, **values: object) -> object:
        self.events.append((event, values))
        return None

    def exception(self, event: str, **values: object) -> object:
        self.events.append((event, values))
        return None


class FakeSearch:
    def __init__(self, result: BusquedaConocimiento) -> None:
        self.result = result
        self.arguments: dict[str, object] = {}

    async def __call__(
        self,
        page: Page,
        numero: str,
        fecha_fin: str,
        evidencia_prefijo: str,
        fecha_inicio: str | None = None,
    ) -> BusquedaConocimiento:
        self.arguments = {
            "page": page,
            "numero": numero,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "evidencia_prefijo": evidencia_prefijo,
        }
        return self.result


def buscar_resultado(
    modalidad: str = "aereo",
    *,
    found: bool = True,
) -> BusquedaConocimiento:
    row = {"nro": "872219087246"} if found else None
    return BusquedaConocimiento(
        numero="872219087246",
        fecha_inicio="",
        fecha_fin="13/07/2026",
        fila=row,
        fila_master={"desc_descarga": "Juan Santamaria"} if found else None,
        modalidad_detectada=modalidad,
    )


def input_data(*, fecha_inicio: date | None = None) -> ConsultaInput:
    return ConsultaInput(
        manifiesto="872219087246",
        fecha_inicio=fecha_inicio,
        fecha_fin=date(2026, 7, 13),
    )


def complete_raw() -> ResultadoEstrategia:
    return {
        "estado": "ok",
        "valores": {
            "fecha_arribo": "01/06/26",
            "transportista": "FEDERAL EXPRESS CORPORATION",
            "movimiento_inventario": "780677",
            "almacen_fiscal": "A283",
            "fecha_ingreso_regimen": "01/06/26",
            "fecha_movimiento_inventario": "02/06/26 00:00",
            "bultos": "1.000",
            "peso_bruto": "3.000",
            "dua_nacionalizacion": "005-2026-392058",
            "fecha_dua": "2026/06/08",
            "estado_final": "Autorizacion de Levante",
        },
    }


def crear_cache() -> InMemoryResultCache:
    return InMemoryResultCache(Settings(cache_ttl_seconds=60))


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [("3.000", 3), ("614.000", 614), ("7450.000", 7450), ("42", 42)],
)
def test_cantidades_tica_interpretan_tres_decimales(
    texto: str,
    esperado: int,
) -> None:
    assert ConsultaOrchestrator._parse_integer(texto) == esperado


@pytest.mark.asyncio
async def test_cada_consulta_emite_evento_operativo_sin_manifiesto() -> None:
    logger = FakeLogger()
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(),
        cache=crear_cache(),
        dispatcher=FakeDispatcher(complete_raw()),
        search=FakeSearch(buscar_resultado()),
        logger=logger,
    )

    await orchestrator.consultar(input_data())

    event, values = logger.events[0]
    assert event == "consulta_tica_finalizada"
    assert values["modalidad"] == "aereo"
    assert values["estado"] == "ok"
    assert isinstance(values["duracion_ms"], float)
    assert "872219087246" not in str(logger.events)


@pytest.mark.asyncio
async def test_flujo_no_migrado_retorna_not_implemented() -> None:
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(),
        cache=crear_cache(),
        dispatcher=PendingMigrationDispatcher(),
        search=FakeSearch(buscar_resultado()),
    )

    result = await orchestrator.consultar(input_data())

    assert result.estado is EstadoConsulta.NOT_IMPLEMENTED
    assert result.modalidad is Modalidad.AEREO
    assert result.motivo == "flujo_modalidad_pendiente_de_migracion"


@pytest.mark.asyncio
async def test_consulta_ok_mapea_datos_y_guarda_cache() -> None:
    cache = crear_cache()
    search = FakeSearch(buscar_resultado())
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(),
        cache=cache,
        dispatcher=FakeDispatcher(complete_raw()),
        search=search,
    )

    result = await orchestrator.consultar(input_data())

    assert result.estado is EstadoConsulta.OK
    assert result.modalidad is Modalidad.AEREO
    assert result.momento3.dua_nacionalizacion == "005-2026-392058"
    assert result.momento3.estado_final == "Autorizacion de Levante"
    assert result.momento2.bultos == 1
    assert result.momento2.peso_bruto == 3
    assert await cache.obtener(Modalidad.AEREO, "872219087246") is not None
    assert search.arguments["fecha_inicio"] is None
    assert search.arguments["fecha_fin"] == "13/07/2026"


@pytest.mark.asyncio
async def test_consulta_envia_fecha_inicio_cuando_fue_proporcionada() -> None:
    search = FakeSearch(buscar_resultado())
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(),
        cache=crear_cache(),
        dispatcher=FakeDispatcher(complete_raw()),
        search=search,
    )

    await orchestrator.consultar(input_data(fecha_inicio=date(2026, 7, 1)))

    assert search.arguments["fecha_inicio"] == "01/07/2026"


@pytest.mark.asyncio
async def test_manifiesto_no_encontrado_retorna_not_found() -> None:
    dispatcher = FakeDispatcher(complete_raw())
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(),
        cache=crear_cache(),
        dispatcher=dispatcher,
        search=FakeSearch(buscar_resultado("no_encontrado", found=False)),
    )

    result = await orchestrator.consultar(input_data())

    assert result.estado is EstadoConsulta.NOT_FOUND
    assert result.modalidad is None
    assert dispatcher.calls == 0


@pytest.mark.asyncio
async def test_conocimiento_sin_arribo_retorna_pending_y_motivo_especifico() -> None:
    cache = crear_cache()
    dispatcher = FakeDispatcher(
        {
            "estado": "sin_arribo",
            "motivo": "arribo_pendiente",
            "valores": {
                "fecha_arribo": "",
                "transportista": "TRANSPORTISTA SANITIZADO",
            },
        }
    )
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(),
        cache=cache,
        dispatcher=dispatcher,
        search=FakeSearch(buscar_resultado()),
    )

    result = await orchestrator.consultar(input_data())

    assert result.estado is EstadoConsulta.PENDING
    assert result.modalidad is Modalidad.AEREO
    assert result.motivo == "arribo_pendiente"
    assert result.momento1.fecha_arribo is None
    assert result.momento2.movimiento_inventario is None
    assert result.momento3.dua_nacionalizacion is None
    assert await cache.cantidad() == 0


@pytest.mark.asyncio
async def test_modalidad_desconocida_retorna_needs_review() -> None:
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(),
        cache=crear_cache(),
        dispatcher=FakeDispatcher(complete_raw()),
        search=FakeSearch(buscar_resultado("desconocida")),
    )

    result = await orchestrator.consultar(input_data())

    assert result.estado is EstadoConsulta.NEEDS_REVIEW
    assert result.modalidad is None


@pytest.mark.asyncio
async def test_browser_caido_sin_cache_retorna_unavailable_sin_inventar_modalidad() -> None:
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(start_error=BrowserUnavailableError(3, "caido")),
        cache=crear_cache(),
        dispatcher=FakeDispatcher(complete_raw()),
        search=FakeSearch(buscar_resultado()),
    )

    result = await orchestrator.consultar(input_data())

    assert result.estado is EstadoConsulta.UNAVAILABLE
    assert result.modalidad is None
    assert result.motivo == "browser_unavailable"


@pytest.mark.asyncio
async def test_browser_caido_con_cache_retorna_stale() -> None:
    cache = crear_cache()
    await cache.guardar(
        ResultadoTICA(
            estado=EstadoConsulta.OK,
            modalidad=Modalidad.AEREO,
            identificador="872219087246",
        )
    )
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(start_error=BrowserUnavailableError(3, "caido")),
        cache=cache,
        dispatcher=FakeDispatcher(complete_raw()),
        search=FakeSearch(buscar_resultado()),
    )

    result = await orchestrator.consultar(input_data())

    assert result.estado is EstadoConsulta.STALE
    assert result.modalidad is Modalidad.AEREO
    assert result.desde_cache is True


@pytest.mark.asyncio
async def test_captcha_retorna_unavailable() -> None:
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(captcha=True),
        cache=crear_cache(),
        dispatcher=FakeDispatcher(complete_raw()),
        search=FakeSearch(buscar_resultado()),
    )

    result = await orchestrator.consultar(input_data())

    assert result.estado is EstadoConsulta.UNAVAILABLE
    assert result.motivo == "captcha_required"


@pytest.mark.asyncio
async def test_flujo_sin_dua_retorna_pending_y_no_se_cachea() -> None:
    cache = crear_cache()
    raw = complete_raw()
    values = cast(dict[str, str], raw["valores"])
    values["dua_nacionalizacion"] = ""
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(),
        cache=cache,
        dispatcher=FakeDispatcher(raw),
        search=FakeSearch(buscar_resultado()),
    )

    result = await orchestrator.consultar(input_data())

    assert result.estado is EstadoConsulta.PENDING
    assert await cache.cantidad() == 0


@pytest.mark.asyncio
async def test_maritimo_multilinea_publica_lista_sin_elegir_escalar() -> None:
    raw = cast(
        ResultadoEstrategia,
        {
            "estado": "ok",
            "valores": {
                "fecha_arribo": "26/05/26",
                "movimientos": [
                    {"movimiento_inventario": "55808682", "bultos": "422.000"},
                    {"movimiento_inventario": "55808690", "bultos": "192.000"},
                ],
                "dua_nacionalizacion": "005-2026-414387",
                "fecha_dua": "2026/06/16",
            },
        },
    )
    orchestrator = ConsultaOrchestrator(
        browser=FakeBrowser(),
        cache=crear_cache(),
        dispatcher=FakeDispatcher(raw),
        search=FakeSearch(buscar_resultado("maritimo")),
    )

    result = await orchestrator.consultar(input_data())

    assert result.modalidad is Modalidad.MARITIMO
    assert result.momento2.movimiento_inventario is None
    assert [item.movimiento_inventario for item in result.momento2.movimientos] == [
        "55808682",
        "55808690",
    ]
    assert [item.bultos for item in result.momento2.movimientos] == [422, 192]
