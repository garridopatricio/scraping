"""Pruebas offline de parsers y regla madre/hijo aerea."""

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.scraper.aereo import (
    MovimientoAereo,
    extraer_deposito,
    extraer_detenciones,
    extraer_dua,
    extraer_totales_dua_anticipado,
    movimientos_desde_filas,
    seleccionar_movimiento_hijo,
)
from app.scraper.domain import extraer_estado_final, limpiar_espacios
from app.scraper.fixture_html import sanitizar_html

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "aereo"


class _TablasHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.filas: list[dict[str, object]] = []
        self._fila: dict[str, object] | None = None
        self._celda: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._fila = {"celdas": [], "enlaces": []}
        elif tag in {"td", "th"} and self._fila is not None:
            self._celda = []
        elif tag == "a" and self._fila is not None:
            href = dict(attrs).get("href")
            if href:
                cast(list[str], self._fila["enlaces"]).append(href)

    def handle_data(self, data: str) -> None:
        if self._celda is not None:
            self._celda.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._fila is not None and self._celda is not None:
            value = " ".join("".join(self._celda).split())
            if value:
                cast(list[str], self._fila["celdas"]).append(value)
            self._celda = None
        elif tag == "tr" and self._fila is not None:
            if self._fila["celdas"]:
                self.filas.append(self._fila)
            self._fila = None


def movimiento(numero: str, consignatario: str = "CONSIGNATARIO-SANITIZADO") -> MovimientoAereo:
    return MovimientoAereo(
        "A283",
        numero,
        "02/06/26 00:00",
        "PK",
        "1.000",
        consignatario,
        f"https://tica/hskmov.aspx?id={numero}",
    )


def test_selecciona_unico_movimiento_ing() -> None:
    candidato = movimiento("200")
    assert seleccionar_movimiento_hijo([candidato]) == candidato


def test_aereo_anticipado_extrae_totales_desde_detalle_dua() -> None:
    texto = "Lugar de Destino: -\nTotal Bultos: 12.000\nTotal Peso: Bruto: 345.000"

    assert extraer_totales_dua_anticipado(texto) == {
        "bultos": "12.000",
        "peso_bruto": "345.000",
    }


def test_ambiguedad_no_adivina() -> None:
    candidatos = [movimiento("100"), movimiento("200")]
    assert seleccionar_movimiento_hijo(candidatos) is None


def test_fila_ING_conserva_enlace_propio() -> None:
    filas = cast(
        list[dict[str, object]],
        [
            {
                "celdas": [
                    "A283",
                    "780677",
                    "X",
                    "X",
                    "02/06/26 00:00",
                    "ING",
                    "PK",
                    "1.000",
                    "HBL-SANITIZADO",
                ],
                "enlaces": ["/TicaExterno/hskmov.aspx?id=780677"],
            }
        ],
    )
    resultado = movimientos_desde_filas(filas)
    assert len(resultado) == 1
    assert resultado[0].movimiento_url.endswith("id=780677")


def test_extrae_detenciones_con_utf8_y_mojibake() -> None:
    texto = (
        "Movimiento: 780677\n"
        "Fecha de Ingr. régimen: 01/06/26\n"
        "Fecha del Movimiento: 02/06/26 00:00\n"
        "Total de Bultos: 1.000\n"
        "Peso: 3.000"
    )
    assert extraer_detenciones(texto)["peso_bruto"] == "3.000"
    assert extraer_deposito("Depósito: A283 ALMACEN SANITIZADO\n") == "A283 ALMACEN SANITIZADO"
    assert extraer_deposito("DepÃ³sito: A283 ALMACEN SANITIZADO\n") == "A283 ALMACEN SANITIZADO"


def test_extrae_dua_confirmado_y_omite_tablas_no_dua() -> None:
    assert extraer_dua([["texto"], ["005", "2026", "392058", "2026/06/08"]]) == {
        "dua_nacionalizacion": "005-2026-392058",
        "fecha_dua": "2026/06/08",
    }


def test_fixtures_estan_sanitizados_y_rotulados() -> None:
    contenido = "\n".join(
        path.read_text(encoding="utf-8") for path in FIXTURE_DIR.rglob("*.html")
    )
    assert "SANITIZADO" in contenido or "SIN-ARRIBO" in contenido
    assert "FEDERAL EXPRESS CORPORATION" not in contenido
    assert "872219087246" not in contenido
    for identificador in (
        "1075388355",
        "72947701231",
        "464524",
        "KUEHNE NAGEL",
        "CEFA CENTRAL FARMACEUTICA",
    ):
        assert identificador not in contenido
    assert not re.search(r"\?[A-Za-z0-9+/]{20}", contenido)


def test_sanitizador_conserva_formato_y_elimina_secretos() -> None:
    resultado = sanitizar_html(
        '<span id="span_CGNROCON_1">1075388355</span>'
        '<a href="hskmov.aspx?token-cifrado-real">1075388355</a>',
        {"1075388355"},
    )
    assert "1075388355" not in resultado
    assert ">9999999999<" in resultado
    assert "hskmov.aspx?PARAMETRO-SANITIZADO" in resultado


def test_fixture_real_stock_es_parseable_y_conserva_enlace_de_fila() -> None:
    parser = _TablasHTML()
    parser.feed(
        (FIXTURE_DIR / "ok_hawb" / "04_afectaciones_stock.html").read_text(
            encoding="utf-8"
        )
    )
    movimientos = movimientos_desde_filas(parser.filas)
    assert len(movimientos) == 1
    assert movimientos[0].movimiento == "55825685"
    assert movimientos[0].movimiento_url.endswith("hskmov.aspx?PARAMETRO-SANITIZADO")


def test_fixture_real_detenciones_alimenta_parser() -> None:
    parser = _TablasHTML()
    parser.feed(
        (FIXTURE_DIR / "ok_hawb" / "06_detenciones.html").read_text(encoding="utf-8")
    )
    texto = "\n".join(
        " ".join(cast(list[str], fila["celdas"])) for fila in parser.filas
    )
    datos = extraer_detenciones(texto)
    assert datos["movimiento_inventario"] == "55825685"
    assert datos["fecha_ingreso_regimen"] == "03/07/26"
    assert datos["bultos"] == "1.000"
    assert datos["peso_bruto"] == "306.000"


def test_fixture_real_dua_conserva_formato_parseable() -> None:
    parser = _TablasHTML()
    parser.feed((FIXTURE_DIR / "ok_hawb" / "07_duas.html").read_text(encoding="utf-8"))
    filas = [cast(list[str], fila["celdas"]) for fila in parser.filas]
    assert extraer_dua(filas)["dua_nacionalizacion"] == "005-2026-999999"


def test_fixture_real_dua_contiene_estado_final_visible() -> None:
    contenido = (FIXTURE_DIR / "ok_hawb" / "08_detalle_dua.html").read_text(
        encoding="utf-8"
    )
    match = re.search(r'id="span_vDUASTSDSC"[^>]*>([^<]*)', contenido)

    assert match is not None
    assert limpiar_espacios(match.group(1)) == "Autorizacion de Levante"


@pytest.mark.asyncio
async def test_estado_final_conserva_otro_texto_visible_y_limpia_espacios() -> None:
    page = MagicMock()
    locator = MagicMock()
    locator.count = AsyncMock(return_value=1)
    locator.first.inner_text = AsyncMock(return_value="  En proceso   de revision  ")
    page.locator.return_value = locator

    assert await extraer_estado_final(page) == "En proceso de revision"
    page.locator.assert_called_once_with("#span_vDUASTSDSC")


@pytest.mark.asyncio
async def test_estado_final_ausente_devuelve_vacio() -> None:
    page = MagicMock()
    locator = MagicMock()
    locator.count = AsyncMock(return_value=0)
    page.locator.return_value = locator

    assert await extraer_estado_final(page) == ""


def test_fixture_real_sin_stock_no_contiene_movimiento_ing() -> None:
    parser = _TablasHTML()
    parser.feed(
        (FIXTURE_DIR / "sin_stock_mawb" / "04_afectaciones_stock.html").read_text(
            encoding="utf-8"
        )
    )
    assert movimientos_desde_filas(parser.filas) == []
