"""Pruebas offline de reglas, parsers y HTML reales maritimos."""

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import cast

from app.scraper.maritimo import (
    DuaMovilizacion,
    completar_dua_movilizacion,
    extraer_dua_movilizacion,
    extraer_lineas,
    lineas_desde_filas,
    movimientos_por_cedula,
    ventana_mes,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "maritimo"


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
            valor = " ".join("".join(self._celda).split())
            if valor:
                cast(list[str], self._fila["celdas"]).append(valor)
            self._celda = None
        elif tag == "tr" and self._fila is not None:
            if self._fila["celdas"]:
                self.filas.append(self._fila)
            self._fila = None


def _filas_fixture(caso: str, archivo: str) -> list[dict[str, object]]:
    parser = _TablasHTML()
    parser.feed((FIXTURE_DIR / caso / archivo).read_text(encoding="utf-8"))
    return parser.filas


def test_extrae_lineas_maritimas() -> None:
    assert extraer_lineas([["1", "228.000", "PK", "2.000", "", "A102", "ALMACEN", "006"]]) == [
        {"linea": "1", "deposito_destino": "A102", "almacen_fiscal": "A102 ALMACEN"}
    ]


def test_dua_movilizacion_permanece_separado() -> None:
    filas = cast(
        list[dict[str, object]],
        [{"celdas": ["006", "2026", "007220", "19/01/26"], "enlaces": ["/hcimdpola.aspx?x"]}],
    )
    dua = extraer_dua_movilizacion(filas, "A102")

    assert dua is not None
    assert dua.dua == "006-2026-007220"
    assert dua.detalle_url.endswith("hcimdpola.aspx?x")


def test_anticipado_conserva_dua_y_no_inventa_destino() -> None:
    original = DuaMovilizacion("006", "2026", "007220", "A102", "19/01/26", "")
    resultado = completar_dua_movilizacion(
        original, "Lugar de Destino: -\nFecha de Registro: 19/01/26 10:00"
    )

    assert resultado.anticipado is True
    assert resultado.dua == "006-2026-007220"
    assert resultado.almacen_destino == ""


def test_consolidado_filtra_cedula_estado_ing_y_conserva_enlaces_de_fila() -> None:
    filas = cast(
        list[dict[str, object]],
        [
            {
                "celdas": [
                    "1458", "2026", "ENT", "19/01/26", "40", "PK",
                    "", "", "", "095144", "ING", "",
                ],
                "enlaces": ["/hskdetent.aspx?uno", "/hskduamov.aspx?uno"],
            },
            {
                "celdas": [
                    "1460", "2026", "ENT", "19/01/26", "30", "PK",
                    "", "", "", "095144", "ING", "",
                ],
                "enlaces": ["/hskdetent.aspx?dos", "/hskduamov.aspx?dos"],
            },
            {
                "celdas": [
                    "9999", "2026", "ENT", "19/01/26", "99", "PK",
                    "", "", "", "OTRA", "ING", "",
                ],
                "enlaces": ["/hskdetent.aspx?otra"],
            },
        ],
    )

    movimientos = movimientos_por_cedula(filas, "095144")

    assert [item.movimiento for item in movimientos] == ["1458", "1460"]
    assert movimientos[0].detenciones_url.endswith("hskdetent.aspx?uno")
    assert movimientos[1].duas_url.endswith("hskduamov.aspx?dos")


def test_ventana_mes_usa_fecha_dua() -> None:
    assert ventana_mes("19/01/26 10:00") == ("01/01/26", "31/01/26")


def test_fixture_real_normal_conserva_una_linea_y_un_movimiento() -> None:
    lineas = lineas_desde_filas(_filas_fixture("normal_una_linea", "03_lineas.html"))
    movimientos = movimientos_por_cedula(
        _filas_fixture("normal_una_linea", "06_deposito_linea_01.html"), "999999"
    )

    assert len(lineas) == 1
    assert len(movimientos) == 1
    assert movimientos[0].movimiento == "99999999"
    assert movimientos[0].detenciones_url.endswith("hskdetent.aspx?PARAMETRO-SANITIZADO")


def test_fixture_real_multilinea_conserva_relacion_fila_enlace() -> None:
    lineas = lineas_desde_filas(
        _filas_fixture("consolidado_multilinea", "03_lineas.html")
    )
    movimientos = []
    for indice in (1, 2):
        movimientos.extend(
            movimientos_por_cedula(
                _filas_fixture(
                    "consolidado_multilinea", f"06_deposito_linea_{indice:02d}.html"
                ),
                "999999",
            )
        )

    assert len(lineas) == 2
    assert len(movimientos) == 2
    assert sum(float(item.bultos) for item in movimientos) == 614
    assert all(item.detenciones_url for item in movimientos)


def test_fixture_real_anticipado_no_incluye_pantalla_deposito() -> None:
    archivos = {path.name for path in (FIXTURE_DIR / "anticipado").glob("*.html")}
    assert len(lineas_desde_filas(_filas_fixture("anticipado", "03_lineas.html"))) == 1
    assert not any(nombre.startswith("06_deposito") for nombre in archivos)


def test_fixtures_maritimos_estan_sanitizados() -> None:
    contenido = "\n".join(
        path.read_text(encoding="utf-8") for path in FIXTURE_DIR.rglob("*.html")
    )
    for identificador in (
        "ENGB2600156",
        "ENGB2600229",
        "E166-26",
        "095144",
        "55791518",
        "55808682",
        "55808690",
        "005-2026-360544",
        "005-2026-414387",
        "002-2026-055881",
        "MAERSK COSTA RICA",
        "MARINA INTERCONTINENTAL",
        "TRANSPORTES INTERNACIONALES TICAL",
    ):
        assert identificador not in contenido
    assert not re.search(r"\?[A-Za-z0-9+/]{20}", contenido)
