"""Pruebas de adaptadores y despacho de modalidad."""

from datetime import date
from typing import cast

import pytest
from playwright.async_api import Page

from app.models import ConsultaInput, Modalidad
from app.scraper.aereo import EstrategiaAerea
from app.scraper.base import FlujoNoMigradoError
from app.scraper.dispatcher import DespachadorEstrategias, ModalidadNoDeterminadaError
from app.scraper.domain import BusquedaConocimiento
from app.scraper.maritimo import EstrategiaMaritima


def crear_busqueda(modalidad: str) -> BusquedaConocimiento:
    return BusquedaConocimiento(
        numero="ENGB2600229",
        fecha_inicio="",
        fecha_fin="13/07/2026",
        fila={"nro": "ENGB2600229"},
        fila_master={"desc_descarga": "Moin"},
        modalidad_detectada=modalidad,
    )


def crear_entrada() -> ConsultaInput:
    return ConsultaInput(manifiesto="ENGB2600229", fecha_fin=date(2026, 7, 13))


@pytest.mark.asyncio
async def test_estrategia_aerea_indica_que_el_flujo_se_migra_en_sprint_2() -> None:
    strategy = EstrategiaAerea()
    page = cast(Page, object())
    busqueda = crear_busqueda("aereo")

    with pytest.raises(FlujoNoMigradoError, match="Sprint 2"):
        await strategy.consultar(page, crear_entrada(), busqueda)


@pytest.mark.asyncio
async def test_estrategia_maritima_indica_que_el_flujo_se_migra_en_sprint_3() -> None:
    strategy = EstrategiaMaritima()
    page = cast(Page, object())
    busqueda = crear_busqueda("maritimo")

    with pytest.raises(FlujoNoMigradoError, match="Sprint 3"):
        await strategy.consultar(page, crear_entrada(), busqueda)


def test_despachador_solo_registra_aereo_y_maritimo() -> None:
    dispatcher = DespachadorEstrategias()

    assert dispatcher.modalidades == frozenset({Modalidad.AEREO, Modalidad.MARITIMO})


def test_despachador_usa_modalidad_ya_detectada() -> None:
    dispatcher = DespachadorEstrategias()

    assert isinstance(dispatcher.obtener(crear_busqueda("aereo")), EstrategiaAerea)
    assert isinstance(dispatcher.obtener(crear_busqueda("maritimo")), EstrategiaMaritima)


@pytest.mark.parametrize("modalidad", ["desconocida", "no_encontrado", "terrestre"])
def test_despachador_rechaza_modalidad_no_soportada(modalidad: str) -> None:
    dispatcher = DespachadorEstrategias()

    with pytest.raises(ModalidadNoDeterminadaError, match="no soportada"):
        dispatcher.obtener(crear_busqueda(modalidad))
