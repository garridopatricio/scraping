"""Tipos y reglas compartidas extraidas de la PoC validada."""

import re
import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page


@dataclass(slots=True)
class BusquedaConocimiento:
    """Resultado de la busqueda inicial de un manifiesto/conocimiento."""

    numero: str
    fecha_inicio: str
    fecha_fin: str
    fila: dict[str, str] | None
    fila_master: dict[str, str] | None
    modalidad_detectada: str


def limpiar_espacios(value: str) -> str:
    """Normaliza espacios y caracteres invisibles comunes del portal."""

    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


async def extraer_estado_final(page: "Page") -> str:
    """Lee la descripcion visible del estado aduanero en el detalle del DUA."""

    locator = page.locator("#span_vDUASTSDSC")
    if await locator.count() == 0:
        return ""
    return limpiar_espacios(await locator.first.inner_text(timeout=5_000))


def normalizar_texto_filtro(value: str) -> str:
    """Normaliza texto para comparar sin tildes ni diferencias de mayusculas."""

    without_accents = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(
        character for character in without_accents if not unicodedata.combining(character)
    )
    return limpiar_espacios(ascii_text).upper()


def clasificar_modalidad_conocimiento(row: dict[str, str] | None) -> str:
    """Clasifica usando ``Desc Descarga`` segun la regla confirmada en Sprint 0."""

    if not row:
        return "no_encontrado"

    destination = normalizar_texto_filtro(row.get("desc_descarga", ""))
    maritime_destinations = {"CALDERA", "MOIN", "PUERTO LIMON"}
    if any(item in destination for item in maritime_destinations):
        return "maritimo"
    if destination:
        return "aereo"
    return "desconocida"
