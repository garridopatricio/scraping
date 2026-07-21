"""Reglas puras del flujo terrestre."""

from datetime import date

import pytest

from app.scraper.terrestre import (
    DuaInvalidoError,
    captcha_data_url,
    es_detalle_dua_url,
    extraer_fecha_registro,
    movimientos_terrestres_desde_filas,
    separar_dua,
)


def test_separa_el_dua_de_prueba() -> None:
    dua = separar_dua(" 005-2026-470211 ")

    assert dua.aduana == "005"
    assert dua.ano == "2026"
    assert dua.numero == "470211"
    assert dua.normalizado == "005-2026-470211"


@pytest.mark.parametrize(
    "value",
    ["005 2026 470211", "  '005 2026 470211'  ", '"005-2026-470211"'],
)
def test_normaliza_espacios_y_comillas_del_dua(value: str) -> None:
    assert separar_dua(value).normalizado == "005-2026-470211"


@pytest.mark.parametrize("value", ["", "005-2026", "A05-2026-1", "005 2026"])
def test_rechaza_duas_sin_tres_grupos_numericos(value: str) -> None:
    with pytest.raises(DuaInvalidoError):
        separar_dua(value)


def test_extrae_fecha_de_registro_y_descarta_la_hora() -> None:
    text = "Fecha de Registro: 2026/07/08\n06:55:36\nTipo de DUA: IMPORTACION"

    assert extraer_fecha_registro(text) == date(2026, 7, 8)


def test_publica_captcha_en_memoria_como_data_url() -> None:
    assert captcha_data_url(b"captcha") == "data:image/png;base64,Y2FwdGNoYQ=="


def test_reconoce_detalle_dua_aunque_tica_agregue_parametros() -> None:
    assert es_detalle_dua_url(
        "https://portaltica.hacienda.go.cr/TicaExterno/hcimdpola.aspx?GXState=abc"
    )


def test_movimiento_terrestre_se_reconoce_por_movimiento_y_detenciones() -> None:
    movimientos = movimientos_terrestres_desde_filas(
        [
            {
                "celdas": ["55825685", "2026", "A134", "Deposito principal", "ING"],
                "enlaces": [
                    "https://tica/hskmov.aspx?movimiento",
                    "https://tica/hskdetent.aspx?detenciones",
                ],
            }
        ]
    )

    assert len(movimientos) == 1
    assert movimientos[0].movimiento == "55825685"
    assert movimientos[0].almacen_fiscal == "A134 Deposito principal"
    assert movimientos[0].detenciones_url.endswith("hskdetent.aspx?detenciones")


def test_movimiento_terrestre_no_exige_columna_ing() -> None:
    movimientos = movimientos_terrestres_desde_filas(
        [
            {
                "celdas": ["2026", "55825685", "A134"],
                "enlaces": ["https://tica/hskdetent.aspx?detenciones"],
            }
        ]
    )

    assert [item.movimiento for item in movimientos] == ["55825685"]
