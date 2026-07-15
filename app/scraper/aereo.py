"""Estrategia productiva para la modalidad aerea de TICA."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

from playwright.async_api import Page

from app.models import ConsultaInput, Modalidad
from app.scraper.base import EstrategiaModalidad, ResultadoEstrategia
from app.scraper.domain import BusquedaConocimiento, limpiar_espacios
from app.scraper.portal import CapturadorHTML

TICA_URL = "https://portaltica.hacienda.go.cr/TicaExterno/"


@dataclass(frozen=True, slots=True)
class MovimientoAereo:
    """Movimiento ING y enlaces pertenecientes a su misma fila."""

    deposito: str
    movimiento: str
    fecha: str
    tipo_bulto: str
    bultos: str
    consignatario: str
    movimiento_url: str


def seleccionar_movimiento_hijo(
    movimientos: list[MovimientoAereo],
) -> MovimientoAereo | None:
    """Acepta el unico ING; no adivina cuando hay varios candidatos."""

    candidatos = [item for item in movimientos if item.movimiento]
    if not candidatos:
        return None

    if len(candidatos) == 1:
        return candidatos[0]
    return None


def extraer_detenciones(texto: str) -> dict[str, str]:
    """Extrae el Momento 2 tolerando tildes y texto legacy mal decodificado."""

    def buscar(pattern: str) -> str:
        match = re.search(pattern, texto, flags=re.IGNORECASE)
        return limpiar_espacios(match.group(1)) if match else ""

    return {
        "movimiento_inventario": buscar(r"Movimiento:\s*([0-9]+)"),
        "fecha_ingreso_regimen": buscar(r"Fecha de Ingr\.\s*r[eéÃ©]gimen:\s*([0-9/]+)"),
        "fecha_movimiento_inventario": buscar(r"Fecha del Movimiento:\s*([0-9/: ]+)"),
        "bultos": buscar(r"Total de Bultos:\s*([0-9.,]+)"),
        "peso_bruto": buscar(r"Peso:\s*([0-9.,]+)"),
    }


def extraer_deposito(texto: str) -> str:
    """Extrae deposito con texto UTF-8 o mojibake heredado."""

    match = re.search(r"Dep(?:ó|Ã³|o)sito:\s*([A-Z0-9]+)\s+([^\n]+)", texto)
    return limpiar_espacios(" ".join(match.groups())) if match else ""


def extraer_dua(filas: list[list[str]]) -> dict[str, str]:
    """Obtiene numero y fecha del primer DUA confirmado de la tabla."""

    for fila in filas:
        numeros = [limpiar_espacios(value) for value in fila]
        if len(numeros) < 4 or not all(value.isdigit() for value in numeros[:3]):
            continue
        return {
            "dua_nacionalizacion": "-".join(numeros[:3]),
            "fecha_dua": next(
                (
                    value
                    for value in numeros[3:]
                    if re.fullmatch(r"[0-9]{2,4}/[0-9]{2}/[0-9]{2,4}", value)
                ),
                "",
            ),
        }
    return {}


async def extraer_dua_desde_pagina(
    page: Page,
    capturador: CapturadorHTML | None = None,
) -> dict[str, str]:
    """Abre el detalle del DUA, fuente prioritaria confirmada por el legacy."""

    datos = extraer_dua(await _filas_texto(page))
    dua = datos.get("dua_nacionalizacion", "")
    numero = dua.rsplit("-", 1)[-1] if dua else ""
    if not numero:
        return datos

    enlace = page.get_by_text(numero, exact=True)
    cantidad = await enlace.count()
    if cantidad == 0:
        return datos
    await enlace.first.click(timeout=10_000)
    await page.wait_for_timeout(3_000)
    if capturador:
        await capturador("08_detalle_dua", page)
    texto = await page.locator("body").inner_text(timeout=5_000)
    match = re.search(r"Fecha (?:de )?Registro:\s*([0-9/: ]+)", texto, flags=re.IGNORECASE)
    if match:
        datos["fecha_dua"] = limpiar_espacios(match.group(1)).split(" ")[0]
    return datos


async def filas_con_enlaces(page: Page) -> list[dict[str, object]]:
    """Lee filas manteniendo cada enlace asociado a su registro."""

    result = await page.locator("table tr").evaluate_all(
        """
        rows => rows.map(row => ({
            celdas: Array.from(row.cells).map(cell => cell.innerText.trim()).filter(Boolean),
            enlaces: Array.from(row.querySelectorAll('a[href]')).map(a => a.href)
        })).filter(row => row.celdas.length)
        """
    )
    return list(result)


def movimientos_desde_filas(filas: list[dict[str, object]]) -> list[MovimientoAereo]:
    """Normaliza solamente movimientos ING con sus enlaces de fila."""

    resultado: list[MovimientoAereo] = []
    for fila in filas:
        celdas_raw = fila.get("celdas")
        enlaces_raw = fila.get("enlaces")
        if not isinstance(celdas_raw, list) or not isinstance(enlaces_raw, list):
            continue
        celdas = [limpiar_espacios(str(value)) for value in celdas_raw]
        if "ING" not in {value.upper() for value in celdas}:
            continue
        enlaces = [str(value) for value in enlaces_raw]
        movimiento_url = next((url for url in enlaces if "hskmov.aspx" in url), "")
        # Columnas confirmadas por la PoC; los campos finales se revalidan en Detenciones.
        resultado.append(
            MovimientoAereo(
                deposito=celdas[0] if celdas else "",
                movimiento=celdas[1] if len(celdas) > 1 else "",
                fecha=celdas[4] if len(celdas) > 4 else "",
                tipo_bulto=celdas[6] if len(celdas) > 6 else "",
                bultos=celdas[7] if len(celdas) > 7 else "",
                consignatario=celdas[10] if len(celdas) > 10 else "",
                movimiento_url=urljoin(TICA_URL, movimiento_url) if movimiento_url else "",
            )
        )
    return resultado


async def _filas_texto(page: Page) -> list[list[str]]:
    result = await page.locator("table tr").evaluate_all(
        "rows => rows.map(r => Array.from(r.cells).map(c => c.innerText.trim()).filter(Boolean))"
    )
    return list(result)


async def _enlace(page: Page, patron: str) -> str:
    enlaces = await page.locator("a[href]").evaluate_all(
        "(links, pattern) => links.map(a => a.href).find(href => href.includes(pattern)) || ''",
        patron,
    )
    return str(enlaces)


class EstrategiaAerea(EstrategiaModalidad):
    """Consulta los tres momentos aereos desde la busqueda compartida."""

    modalidad = Modalidad.AEREO

    def __init__(self, capturador: CapturadorHTML | None = None) -> None:
        self.capturador = capturador

    async def _capturar(self, nombre: str, page: Page) -> None:
        if self.capturador:
            await self.capturador(nombre, page)

    async def consultar(
        self,
        page: Page,
        entrada: ConsultaInput,
        busqueda: BusquedaConocimiento,
    ) -> ResultadoEstrategia:
        fila = busqueda.fila or {}
        valores = {
            "fecha_arribo": fila.get("fecha_arribo", ""),
            "transportista": (busqueda.fila_master or fila).get("razon_social", ""),
        }
        if not valores["fecha_arribo"]:
            return {
                "estado": "sin_arribo",
                "motivo": "arribo_pendiente",
                "valores": valores,
            }

        lineas_url = await _enlace(page, "hcglineas.aspx")
        if not lineas_url:
            return {"estado": "sin_dua", "valores": valores}
        await page.goto(lineas_url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(3_000)
        await self._capturar("03_lineas", page)

        afectaciones_url = await _enlace(page, "hcgafeli.aspx")
        if not afectaciones_url:
            return {"estado": "sin_dua", "valores": valores}
        await page.goto(afectaciones_url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(3_000)
        await self._capturar("04_afectaciones_stock", page)

        movimientos = movimientos_desde_filas(await filas_con_enlaces(page))
        seleccionado = seleccionar_movimiento_hijo(movimientos)
        if seleccionado is None and len(movimientos) > 1:
            return {
                "estado": "needs_review",
                "motivo": "ambiguedad_madre_hijo",
                "valores": valores,
            }
        if seleccionado is None or not seleccionado.movimiento_url:
            return {"estado": "sin_dua", "valores": valores}

        valores.update(
            {
                "movimiento_inventario": seleccionado.movimiento,
                "fecha_movimiento_inventario": seleccionado.fecha,
                "bultos": seleccionado.bultos,
            }
        )
        await page.goto(seleccionado.movimiento_url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(3_000)
        await self._capturar("05_movimiento", page)
        texto = await page.locator("body").inner_text(timeout=5_000)
        valores["almacen_fiscal"] = extraer_deposito(texto)

        detenciones_url = await _enlace(page, "hskdetent.aspx")
        duas_url = await _enlace(page, "hskduamov.aspx")
        if detenciones_url:
            await page.goto(detenciones_url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(3_000)
            await self._capturar("06_detenciones", page)
            valores.update(
                extraer_detenciones(await page.locator("body").inner_text(timeout=5_000))
            )
        if duas_url:
            await page.goto(duas_url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(3_000)
            await self._capturar("07_duas", page)
            valores.update(await extraer_dua_desde_pagina(page, self.capturador))

        return {
            "estado": "ok" if valores.get("dua_nacionalizacion") else "sin_dua",
            "valores": valores,
        }
