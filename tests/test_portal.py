"""Pruebas de las reglas productivas extraidas de la PoC."""

from app.scraper.domain import clasificar_modalidad_conocimiento
from app.scraper.portal import (
    extraer_url_master,
    normalizar_fila_conocimiento,
    normalizar_fila_master_conocimiento,
)


def test_clasifica_puertos_como_maritimos_y_otras_descargas_como_aereas() -> None:
    assert clasificar_modalidad_conocimiento({"desc_descarga": "Puerto de Moín"}) == "maritimo"
    assert clasificar_modalidad_conocimiento({"desc_descarga": "Aeropuerto Santamaría"}) == "aereo"


def test_normaliza_columnas_confirmadas_del_conocimiento() -> None:
    row = [""] * 23
    row[4] = "13/07/2026"
    row[8] = "ENGB2600229"
    row[15] = "Moin"
    row[16] = "MASTER-1"

    result = normalizar_fila_conocimiento(row)

    assert result["fecha_arribo"] == "13/07/2026"
    assert result["nro"] == "ENGB2600229"
    assert result["desc_descarga"] == "Moin"
    assert result["master"] == "MASTER-1"


def test_normaliza_fila_master_con_celda_inicial_vacia() -> None:
    row = ["", "1", "BL-1", "H", "RUC", "Transportista", "LIM", "Puerto Limon"]

    result = normalizar_fila_master_conocimiento(row)

    assert result["nro"] == "1"
    assert result["razon_social"] == "Transportista"
    assert result["desc_descarga"] == "Puerto Limon"


def test_extrae_enlace_master_que_corresponde_a_la_fila() -> None:
    links = [
        {"texto": "OTRO", "href": "https://tica/hcgconspadre.aspx?id=1"},
        {"texto": "MASTER-1", "href": "https://tica/hcgconspadre.aspx?id=2"},
    ]

    result = extraer_url_master(links, {"master": "MASTER-1"})

    assert result == "https://tica/hcgconspadre.aspx?id=2"
