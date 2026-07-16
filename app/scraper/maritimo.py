"""Estrategia productiva para la modalidad maritima de TICA."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import Page

from app.config import Settings, get_settings
from app.models import ConsultaInput, Modalidad
from app.scraper.aereo import extraer_detenciones
from app.scraper.base import EstrategiaModalidad, ResultadoEstrategia
from app.scraper.domain import BusquedaConocimiento, extraer_estado_final, limpiar_espacios
from app.scraper.portal import CapturadorHTML

TICA_URL = "https://portaltica.hacienda.go.cr/TicaExterno/"


@dataclass(frozen=True, slots=True)
class DuaMovilizacion:
    aduana: str
    anio: str
    numero: str
    deposito_destino: str
    fecha: str
    detalle_url: str
    lugar_destino: str = ""
    almacen_destino: str = ""
    anticipado: bool = False

    @property
    def dua(self) -> str:
        return "-".join((self.aduana, self.anio, self.numero))


@dataclass(frozen=True, slots=True)
class MovimientoDeposito:
    movimiento: str
    fecha_ingreso_regimen: str
    bultos: str
    detenciones_url: str
    duas_url: str


@dataclass(frozen=True, slots=True)
class LineaMaritima:
    numero: str
    deposito_destino: str
    almacen_fiscal: str
    afectaciones_url: str


def solo_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor)


def ventana_mes(fecha: str) -> tuple[str, str]:
    valor = limpiar_espacios(fecha).split(" ")[0]
    parsed: datetime | None = None
    for formato in ("%d/%m/%y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(valor, formato)
            break
        except ValueError:
            continue
    if parsed is None:
        return "01/01/26", "31/01/26"
    ultimo = calendar.monthrange(parsed.year, parsed.month)[1]
    return (
        f"01/{parsed.month:02d}/{parsed.year % 100:02d}",
        f"{ultimo:02d}/{parsed.month:02d}/{parsed.year % 100:02d}",
    )


def extraer_lineas(filas: list[list[str]]) -> list[dict[str, str]]:
    resultado: list[dict[str, str]] = []
    for fila in filas:
        if len(fila) < 8 or not fila[0].isdigit():
            continue
        deposito = limpiar_espacios(fila[5])
        if not re.fullmatch(r"[A-Z][0-9]{3}", deposito):
            continue
        resultado.append(
            {
                "linea": limpiar_espacios(fila[0]),
                "deposito_destino": deposito,
                "almacen_fiscal": limpiar_espacios(f"{deposito} {fila[6]}"),
            }
        )
    return resultado


def lineas_desde_filas(filas: list[dict[str, object]]) -> list[LineaMaritima]:
    resultado: list[LineaMaritima] = []
    for fila in filas:
        cells_raw = fila.get("celdas")
        links_raw = fila.get("enlaces")
        if not isinstance(cells_raw, list) or not isinstance(links_raw, list):
            continue
        cells = [limpiar_espacios(str(value)) for value in cells_raw]
        if len(cells) < 8 or not cells[0].isdigit():
            continue
        deposito = cells[5]
        if not re.fullmatch(r"[A-Z][0-9]{3}", deposito):
            continue
        links = [str(value) for value in links_raw]
        afectaciones = next((url for url in links if "hcgafeli.aspx" in url), "")
        if not afectaciones:
            continue
        resultado.append(
            LineaMaritima(
                numero=cells[0],
                deposito_destino=deposito,
                almacen_fiscal=limpiar_espacios(f"{deposito} {cells[6]}"),
                afectaciones_url=urljoin(TICA_URL, afectaciones),
            )
        )
    return resultado


def extraer_dua_movilizacion(
    filas: list[dict[str, object]],
    deposito_destino: str,
) -> DuaMovilizacion | None:
    for fila in filas:
        cells_raw = fila.get("celdas")
        links_raw = fila.get("enlaces")
        if not isinstance(cells_raw, list) or not isinstance(links_raw, list):
            continue
        cells = [limpiar_espacios(str(value)) for value in cells_raw]
        if len(cells) < 3 or not all(value.isdigit() for value in cells[:3]):
            continue
        links = [str(value) for value in links_raw]
        detalle = next((url for url in links if "hcimdpola.aspx" in url), "")
        fecha = next(
            (value for value in cells[3:] if re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{2,4}", value)),
            "",
        )
        return DuaMovilizacion(
            aduana=cells[0],
            anio=cells[1],
            numero=cells[2],
            deposito_destino=deposito_destino,
            fecha=fecha,
            detalle_url=urljoin(TICA_URL, detalle) if detalle else "",
        )
    return None


def completar_dua_movilizacion(dua: DuaMovilizacion, texto: str) -> DuaMovilizacion:
    destino_match = re.search(r"Lugar de Destino:\s*([^\n]+)", texto, flags=re.IGNORECASE)
    destino = limpiar_espacios(destino_match.group(1)) if destino_match else ""
    deposito = dua.deposito_destino
    almacen = ""
    destino_valido = re.fullmatch(r"([A-Z][0-9]{3})\s*-\s*(.+)", destino)
    if destino_valido:
        deposito = limpiar_espacios(destino_valido.group(1))
        almacen = limpiar_espacios(destino_valido.group(2))
    fecha_match = re.search(r"Fecha (?:de )?Registro:\s*([0-9/: ]+)", texto, re.IGNORECASE)
    return DuaMovilizacion(
        aduana=dua.aduana,
        anio=dua.anio,
        numero=dua.numero,
        deposito_destino=deposito,
        fecha=limpiar_espacios(fecha_match.group(1)) if fecha_match else dua.fecha,
        detalle_url=dua.detalle_url,
        lugar_destino=destino,
        almacen_destino=almacen,
        anticipado=almacen == "",
    )


def extraer_totales_dua_anticipado(texto: str) -> dict[str, str]:
    bultos_match = re.search(r"Total\s+Bultos:\s*([0-9.,]+)", texto, re.IGNORECASE)
    peso_match = re.search(
        r"Total\s+Peso:\s*Bruto:\s*([0-9.,]+)", texto, re.IGNORECASE
    )
    resultado: dict[str, str] = {}
    if bultos_match:
        resultado["bultos"] = limpiar_espacios(bultos_match.group(1))
    if peso_match:
        resultado["peso_bruto"] = limpiar_espacios(peso_match.group(1))
    return resultado


def movimientos_por_cedula(
    filas: list[dict[str, object]],
    cedula: str,
) -> list[MovimientoDeposito]:
    buscada = solo_digitos(cedula)
    resultado: list[MovimientoDeposito] = []
    for fila in filas:
        cells_raw = fila.get("celdas")
        links_raw = fila.get("enlaces")
        if not isinstance(cells_raw, list) or not isinstance(links_raw, list):
            continue
        cells = [limpiar_espacios(str(value)) for value in cells_raw]
        if len(cells) < 12:
            continue
        consignatario = solo_digitos(cells[9])
        if buscada not in consignatario or cells[10].upper() != "ING":
            continue
        links = [str(value) for value in links_raw]
        resultado.append(
            MovimientoDeposito(
                movimiento=cells[0],
                fecha_ingreso_regimen=cells[3],
                bultos=cells[4],
                detenciones_url=next(
                    (urljoin(TICA_URL, url) for url in links if "hskdetent.aspx" in url), ""
                ),
                duas_url=next(
                    (urljoin(TICA_URL, url) for url in links if "hskduamov.aspx" in url), ""
                ),
            )
        )
    return resultado


async def filas_texto(page: Page) -> list[list[str]]:
    result = await page.locator("table tr").evaluate_all(
        "rows => rows.map(r => Array.from(r.cells).map(c => c.innerText.trim()).filter(Boolean))"
    )
    return list(result)


async def filas_enlaces(page: Page) -> list[dict[str, object]]:
    result = await page.locator("table tr").evaluate_all(
        """
        rows => rows.map(row => ({
            celdas: Array.from(row.cells).map(cell => cell.innerText.trim()).filter(Boolean),
            enlaces: Array.from(row.querySelectorAll('a[href]')).map(a => a.href)
        })).filter(row => row.celdas.length)
        """
    )
    return list(result)


async def enlace(page: Page, patron: str) -> str:
    result = await page.locator("a[href]").evaluate_all(
        "(links, p) => links.map(a => a.href).find(href => href.includes(p)) || ''", patron
    )
    return str(result)


async def dua_desde_pagina(page: Page, capturador: CapturadorHTML | None) -> dict[str, str]:
    for fila in await filas_texto(page):
        if len(fila) < 3 or not all(value.isdigit() for value in fila[:3]):
            continue
        dua = "-".join(fila[:3])
        locator = page.get_by_text(fila[2], exact=True).first
        fecha = ""
        estado_final = ""
        if await locator.count():
            await locator.click(timeout=10_000)
            await page.wait_for_timeout(3_000)
            if capturador:
                await capturador("09_detalle_dua_nacionalizacion", page)
            texto = await page.locator("body").inner_text(timeout=5_000)
            estado_final = await extraer_estado_final(page)
            match = re.search(r"Fecha (?:de )?Registro:\s*([0-9/: ]+)", texto, re.IGNORECASE)
            if match:
                fecha = limpiar_espacios(match.group(1)).split(" ")[0]
        return {
            "dua_nacionalizacion": dua,
            "fecha_dua": fecha,
            "estado_final": estado_final,
        }
    return {}


class EstrategiaMaritima(EstrategiaModalidad):
    modalidad = Modalidad.MARITIMO

    def __init__(
        self,
        settings: Settings | None = None,
        capturador: CapturadorHTML | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.capturador = capturador

    async def _capturar(self, nombre: str, page: Page) -> None:
        if self.capturador:
            await self.capturador(nombre, page)

    async def _buscar_deposito(
        self,
        page: Page,
        dua_mov: DuaMovilizacion,
        indice_linea: int,
    ) -> list[MovimientoDeposito]:
        inicio, fin = ventana_mes(dua_mov.fecha)
        await page.goto(f"{TICA_URL}hskmovstk.aspx", wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(2_000)
        await page.locator("#vVRGDEPID").fill(dua_mov.deposito_destino)
        await page.locator("#vVFCHINI").fill(inicio)
        await page.locator("#vVFCHFIN").fill(fin)
        await page.locator("#vCGADUAN").fill(dua_mov.aduana)
        await page.locator("#vCGANOPRESE").fill(dua_mov.anio)
        await page.locator("#vCGDOCNRO").fill(dua_mov.numero)
        await page.locator("#vVCGMOVTPO").select_option("TOD")
        await page.locator('input[name="BUTTON1"]').click(timeout=10_000)
        await page.wait_for_timeout(5_000)
        await self._capturar(f"06_deposito_linea_{indice_linea:02d}", page)
        return movimientos_por_cedula(
            await filas_enlaces(page), self.settings.cedula_juridica_maritima
        )

    async def consultar(
        self,
        page: Page,
        entrada: ConsultaInput,
        busqueda: BusquedaConocimiento,
    ) -> ResultadoEstrategia:
        fila = busqueda.fila or {}
        valores: dict[str, object] = {
            "fecha_arribo": fila.get("fecha_arribo", ""),
            "transportista": (busqueda.fila_master or fila).get("razon_social", ""),
            "movimientos": [],
        }
        if not valores["fecha_arribo"]:
            return {"estado": "sin_arribo", "motivo": "arribo_pendiente", "valores": valores}

        lineas_url = await enlace(page, "hcglineas.aspx")
        if not lineas_url:
            return {"estado": "sin_dua", "motivo": "dua_movilizacion_pendiente", "valores": valores}
        await page.goto(lineas_url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(3_000)
        await self._capturar("03_lineas", page)
        lineas = lineas_desde_filas(await filas_enlaces(page))
        if not lineas:
            return {"estado": "sin_dua", "motivo": "lineas_pendientes", "valores": valores}

        candidatos_detallados: list[tuple[MovimientoDeposito, DuaMovilizacion]] = []
        duas_urls: list[str] = []
        linea_incompleta = False
        for indice_linea, linea in enumerate(lineas, start=1):
            detalle_dua_texto = ""
            await page.goto(
                linea.afectaciones_url,
                wait_until="domcontentloaded",
                timeout=30_000,
            )
            await page.wait_for_timeout(3_000)
            await self._capturar(f"04_afectaciones_linea_{indice_linea:02d}", page)
            dua_mov = extraer_dua_movilizacion(
                await filas_enlaces(page), linea.deposito_destino
            )
            if dua_mov is None:
                linea_incompleta = True
                continue
            if dua_mov.detalle_url:
                await page.goto(
                    dua_mov.detalle_url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                await page.wait_for_timeout(3_000)
                await self._capturar(
                    f"05_detalle_dua_movilizacion_linea_{indice_linea:02d}", page
                )
                detalle_dua_texto = await page.locator("body").inner_text(timeout=5_000)
                dua_mov = completar_dua_movilizacion(dua_mov, detalle_dua_texto)
            if dua_mov.anticipado:
                valores.update(
                    {
                        "dua_nacionalizacion": dua_mov.dua,
                        "fecha_dua": dua_mov.fecha.split(" ")[0],
                        "estado_final": await extraer_estado_final(page),
                        **extraer_totales_dua_anticipado(detalle_dua_texto),
                    }
                )
                return {
                    "estado": "ok",
                    "motivo": "pedido_anticipado",
                    "valores": valores,
                }
            candidatos_linea = await self._buscar_deposito(page, dua_mov, indice_linea)
            if not candidatos_linea:
                linea_incompleta = True
                continue
            candidatos_detallados.extend((item, dua_mov) for item in candidatos_linea)
            duas_urls.extend(item.duas_url for item in candidatos_linea if item.duas_url)

        if not candidatos_detallados:
            return {
                "estado": "no_encontrado",
                "motivo": "cedula_no_encontrada",
                "valores": valores,
            }

        movimientos: list[dict[str, str]] = []
        movimientos_vistos: set[str] = set()
        for indice, (candidato, dua_mov) in enumerate(candidatos_detallados, start=1):
            if candidato.movimiento in movimientos_vistos:
                continue
            movimientos_vistos.add(candidato.movimiento)
            datos = {
                "movimiento_inventario": candidato.movimiento,
                "almacen_fiscal": limpiar_espacios(
                    f"{dua_mov.deposito_destino} {dua_mov.almacen_destino}"
                ),
                "fecha_ingreso_regimen": candidato.fecha_ingreso_regimen,
                "bultos": candidato.bultos,
            }
            if candidato.detenciones_url:
                await page.goto(
                    candidato.detenciones_url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                await page.wait_for_timeout(3_000)
                await self._capturar(f"07_detenciones_{indice:02d}", page)
                datos.update(
                    extraer_detenciones(
                        await page.locator("body").inner_text(timeout=5_000)
                    )
                )
            movimientos.append(datos)

        valores["movimientos"] = movimientos
        if len(movimientos) == 1:
            valores.update(movimientos[0])

        if linea_incompleta:
            return {
                "estado": "sin_dua",
                "motivo": "linea_maritima_pendiente",
                "valores": valores,
            }

        duas_url = next(iter(dict.fromkeys(duas_urls)), "")
        if not duas_url:
            return {
                "estado": "sin_dua",
                "motivo": "dua_nacionalizacion_pendiente",
                "valores": valores,
            }
        await page.goto(duas_url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(3_000)
        await self._capturar("08_duas_deposito", page)
        valores.update(await dua_desde_pagina(page, self.capturador))
        return {
            "estado": "ok" if valores.get("dua_nacionalizacion") else "sin_dua",
            "motivo": (
                None
                if valores.get("dua_nacionalizacion")
                else "dua_nacionalizacion_pendiente"
            ),
            "valores": valores,
        }
