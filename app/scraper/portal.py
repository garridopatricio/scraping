"""Navegacion productiva compartida para la busqueda inicial en TICA."""

from typing import cast

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from app.scraper.captcha import CaptchaRequiredError, contiene_captcha
from app.scraper.domain import (
    BusquedaConocimiento,
    clasificar_modalidad_conocimiento,
    limpiar_espacios,
)

TICA_URL = "https://portaltica.hacienda.go.cr/TicaExterno/"


async def buscar_conocimiento(
    page: Page,
    numero: str,
    fecha_fin: str,
    evidencia_prefijo: str,
    fecha_inicio: str | None = None,
) -> BusquedaConocimiento:
    """Busca una vez el conocimiento y lee Master para clasificar la modalidad."""

    _ = evidencia_prefijo  # Reservado para observabilidad/evidencias configurables.
    await ir_a_conocimientos_embarque(page)
    if contiene_captcha(await texto_pagina(page)):
        raise CaptchaRequiredError("La pantalla de conocimientos requiere CAPTCHA")

    if fecha_inicio:
        await page.locator("#vVFCH1").fill(fecha_inicio)
    await page.locator("#vVFCHF").fill(fecha_fin)
    await page.locator("#vCGNROCON").fill(numero)
    await page.locator('input[name="BTN_ENTER1"]').click(timeout=10_000)
    await page.wait_for_timeout(4_000)

    found = await extraer_fila_conocimiento_con_links(page, numero)
    row = found[0] if found else None
    master_url = found[1] if found else None
    master_row = await extraer_fila_master_conocimiento(page, master_url)
    if row and master_row:
        row["razon_social"] = master_row.get("razon_social", "") or row.get(
            "razon_social", ""
        )
        row["descarga"] = master_row.get("descarga", "") or row.get("descarga", "")
        row["desc_descarga"] = master_row.get("desc_descarga", "") or row.get(
            "desc_descarga", ""
        )

    return BusquedaConocimiento(
        numero=numero,
        fecha_inicio=fecha_inicio or "",
        fecha_fin=fecha_fin,
        fila=row,
        fila_master=master_row,
        modalidad_detectada=clasificar_modalidad_conocimiento(master_row or row),
    )


async def ir_a_conocimientos_embarque(page: Page) -> None:
    """Abre la pantalla publica de Conocimientos de Embarque."""

    await page.goto(TICA_URL, wait_until="domcontentloaded", timeout=30_000)
    await page.wait_for_timeout(1_500)
    await page.goto(f"{TICA_URL}hcgwebmain.aspx", wait_until="domcontentloaded", timeout=30_000)
    await page.wait_for_timeout(1_500)
    await page.get_by_text("Conocimientos de Embarque", exact=True).click(timeout=10_000)
    await page.wait_for_timeout(2_000)


async def texto_pagina(page: Page) -> str:
    """Lee el texto visible sin convertir un fallo secundario en error de negocio."""

    try:
        return await page.locator("body").inner_text(timeout=5_000)
    except PlaywrightError:
        return ""


async def filas_tablas(page: Page) -> list[list[str]]:
    """Lee las filas visibles de todas las tablas."""

    result = await page.locator("table tr").evaluate_all(
        """
        rows => rows.map(row =>
            Array.from(row.cells).map(cell => cell.innerText.trim()).filter(Boolean)
        ).filter(cells => cells.length)
        """
    )
    return cast(list[list[str]], result)


async def extraer_fila_conocimiento_con_links(
    page: Page,
    conocimiento: str,
) -> tuple[dict[str, str], str | None] | None:
    """Obtiene la fila del conocimiento y la URL de su Master."""

    result = await page.locator("table tr").evaluate_all(
        """
        rows => rows.map(row => ({
            celdas: Array.from(row.cells).map(cell => cell.innerText.trim()),
            links: Array.from(row.querySelectorAll('a[href]')).map(a => ({
                texto: a.innerText.trim(),
                href: a.href
            }))
        })).filter(row => row.celdas.some(Boolean))
        """
    )
    rows = cast(list[dict[str, object]], result)

    for item in rows:
        raw_cells = item.get("celdas")
        if not isinstance(raw_cells, list):
            continue
        cells = [str(cell) for cell in raw_cells]
        if conocimiento not in cells:
            continue
        normalized = normalizar_fila_conocimiento(cells)
        return normalized, extraer_url_master(item.get("links"), normalized)
    return None


def extraer_url_master(links: object, row: dict[str, str]) -> str | None:
    """Selecciona el enlace de la columna Master de la fila encontrada."""

    if not isinstance(links, list):
        return None
    master = limpiar_espacios(row.get("master", ""))
    for item in links:
        if not isinstance(item, dict):
            continue
        href = str(item.get("href", ""))
        text = limpiar_espacios(str(item.get("texto", "")))
        if "hcgconspadre.aspx" in href and (not master or text == master):
            return href
    return None


async def extraer_fila_master_conocimiento(
    page: Page,
    master_url: str | None,
) -> dict[str, str] | None:
    """Abre Master y extrae transportista y descarga reales."""

    if not master_url:
        return None

    await page.goto(master_url, wait_until="domcontentloaded", timeout=30_000)
    await page.wait_for_timeout(3_000)
    try:
        for row in await filas_tablas(page):
            if len(row) < 7:
                continue
            start = 1 if not row[0] else 0
            if not valor_en_indice(row, start).isdigit() or not valor_en_indice(row, start + 1):
                continue
            return normalizar_fila_master_conocimiento(row)
        return None
    finally:
        await page.go_back(wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(1_500)


def normalizar_fila_conocimiento(row: list[str]) -> dict[str, str]:
    """Asigna los nombres confirmados a las columnas del conocimiento."""

    fields = [
        "modalidad",
        "tipo",
        "manifiesto",
        "ingreso",
        "fecha_arribo",
        "viajes",
        "viajes_link",
        "lineas",
        "nro",
        "courier",
        "categoria",
        "tipo_conocimiento",
        "ruc_garante",
        "razon_social",
        "descarga",
        "desc_descarga",
        "master",
        "embarque",
        "desc_embarque",
        "columna_extra_1",
        "columna_extra_2",
        "columna_extra_3",
        "estado",
    ]
    return {field: valor_en_indice(row, index) for index, field in enumerate(fields)}


def normalizar_fila_master_conocimiento(row: list[str]) -> dict[str, str]:
    """Asigna nombres a las columnas confirmadas de Master."""

    start = 1 if row and not row[0] else 0
    return {
        "nro": valor_en_indice(row, start),
        "bl_original": valor_en_indice(row, start + 1),
        "tipo_conocimiento": valor_en_indice(row, start + 2),
        "ruc_garante": valor_en_indice(row, start + 3),
        "razon_social": valor_en_indice(row, start + 4),
        "descarga": valor_en_indice(row, start + 5),
        "desc_descarga": valor_en_indice(row, start + 6),
        "master": valor_en_indice(row, start + 7),
        "embarque": valor_en_indice(row, start + 8),
        "desc_embarque": valor_en_indice(row, start + 9),
        "estado": valor_en_indice(row, start + 13) or valor_en_indice(row, start + 9),
    }


def valor_en_indice(row: list[str], index: int) -> str:
    """Lee una columna sin fallar cuando TICA devuelve una fila corta."""

    if index >= len(row):
        return ""
    return limpiar_espacios(row[index])

