"""Consulta terrestre de DUA con CAPTCHA resuelto manualmente por Dokka."""

from __future__ import annotations

import asyncio
import base64
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from time import perf_counter
from urllib.parse import urlparse
from uuid import uuid4

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright
from playwright.async_api import Error as PlaywrightError

from app.config import Settings, get_settings
from app.observability import obtener_logger
from app.scraper.aereo import (
    extraer_deposito,
    extraer_detenciones,
    extraer_totales_dua_anticipado,
    filas_con_enlaces,
    movimientos_desde_filas,
)

FORM_PATH = "hcimppon.aspx"
DETAIL_PATH = "/hcimdpola.aspx"
DUA_PATTERN = re.compile(r"^(\d+)(?:\s*-\s*|\s+)(\d+)(?:\s*-\s*|\s+)(\d+)$")
DATE_PATTERN = re.compile(
    r"Fecha\s+de\s+Registro\s*:\s*(\d{4})[/-](\d{1,2})[/-](\d{1,2})",
    re.IGNORECASE,
)


class EstadoSesionTerrestre(StrEnum):
    INICIANDO = "iniciando"
    ESPERANDO_CAPTCHA = "esperando_captcha"
    CONSULTANDO = "consultando"
    COMPLETADO = "completado"
    EXPIRADO = "expirado"
    CANCELADO = "cancelado"
    FALLIDO = "fallido"


class TerrestreError(RuntimeError):
    """Error de dominio controlado para la API terrestre."""


class DuaInvalidoError(TerrestreError):
    pass


class SesionNoEncontradaError(TerrestreError):
    pass


class LimiteSesionesError(TerrestreError):
    pass


class DuaNoEncontradoError(TerrestreError):
    pass


@dataclass(frozen=True, slots=True)
class PartesDua:
    aduana: str
    ano: str
    numero: str

    @property
    def normalizado(self) -> str:
        return f"{self.aduana}-{self.ano}-{self.numero}"


@dataclass(frozen=True, slots=True)
class MovimientoTerrestre:
    movimiento: str
    almacen_fiscal: str
    movimiento_url: str
    detenciones_url: str


def separar_dua(value: str) -> PartesDua:
    normalized = value.strip().strip("\"'").strip()
    match = DUA_PATTERN.fullmatch(normalized)
    if match is None:
        raise DuaInvalidoError("El DUA debe contener tres grupos numericos separados por guiones.")
    return PartesDua(*match.groups())


@dataclass(slots=True)
class SesionTerrestre:
    session_id: str
    dua: PartesDua
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page
    captcha: bytes
    expires_at: datetime
    estado: EstadoSesionTerrestre = EstadoSesionTerrestre.ESPERANDO_CAPTCHA
    expiry_task: asyncio.Task[None] | None = None
    processing_task: asyncio.Task[None] | None = None
    resultado: dict[str, object] | None = None
    error: str | None = None
    correlacion_id: str = ""
    iniciada_en: float = 0.0


class TerrestreSessionManager:
    """Conserva las paginas TICA solo mientras el humano resuelve el CAPTCHA."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._sessions: dict[str, SesionTerrestre] = {}
        self._starting_sessions = 0
        self._registry_lock = asyncio.Lock()
        self._navigation_lock = asyncio.Lock()
        self._logger = obtener_logger(__name__)

    async def iniciar(self, dua_value: str) -> SesionTerrestre:
        dua = separar_dua(dua_value)
        await self._limpiar_expiradas()
        async with self._registry_lock:
            if (
                len(self._sessions) + self._starting_sessions
                >= self.settings.terrestrial_max_sessions
            ):
                raise LimiteSesionesError("Se alcanzo el limite de consultas terrestres activas.")
            self._starting_sessions += 1

        playwright = await async_playwright().start()
        browser: Browser | None = None
        context: BrowserContext | None = None
        try:
            try:
                browser = await playwright.chromium.launch(
                    channel="chrome",
                    headless=self.settings.browser_headless,
                )
            except PlaywrightError:
                browser = await playwright.chromium.launch(
                    headless=self.settings.browser_headless
                )
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            page = await context.new_page()
            page.set_default_timeout(self.settings.browser_timeout_ms)
            async with self._navigation_lock:
                await page.goto(
                    f"{self.settings.base_url.rstrip('/')}/{FORM_PATH}",
                    wait_until="domcontentloaded",
                    timeout=self.settings.browser_timeout_ms,
                )
                await page.locator("#vVCODI_ADUA").fill(dua.aduana)
                await page.locator("#vVANO_PRE").fill(dua.ano)
                await page.locator("#vVNUME_CORR").fill(dua.numero)
                captcha = await self._capturar_captcha(page)

            session = SesionTerrestre(
                session_id=secrets.token_urlsafe(32),
                dua=dua,
                playwright=playwright,
                browser=browser,
                context=context,
                page=page,
                captcha=captcha,
                expires_at=datetime.now(UTC)
                + timedelta(seconds=self.settings.terrestrial_session_ttl_seconds),
                correlacion_id=uuid4().hex,
                iniciada_en=perf_counter(),
            )
            async with self._registry_lock:
                self._sessions[session.session_id] = session
                self._starting_sessions -= 1
            session.expiry_task = asyncio.create_task(
                self._expire_after(session.session_id),
                name=f"expire-terrestrial-{session.session_id}",
            )
            self._logger.info(
                "consulta_tica_iniciada",
                correlacion_id=session.correlacion_id,
                tipo_busqueda="dua",
                numero_busqueda=session.dua.normalizado,
                modalidad="terrestre",
                estado=session.estado.value,
            )
            return session
        except BaseException:
            async with self._registry_lock:
                self._starting_sessions -= 1
            if context is not None:
                await context.close()
            if browser is not None:
                await browser.close()
            await playwright.stop()
            raise

    async def resolver(self, session_id: str, captcha: str) -> tuple[str, SesionTerrestre]:
        session = await self._obtener(session_id)
        session.estado = EstadoSesionTerrestre.CONSULTANDO
        try:
            async with self._navigation_lock:
                await session.page.locator("input[name='cfield']").fill(captcha.strip())
                await session.page.locator("input[name='DETALLE']").click()
                accepted = await self._esperar_resultado_captcha(session.page)

            if not accepted:
                session.estado = EstadoSesionTerrestre.ESPERANDO_CAPTCHA
                self._logger.info(
                    "captcha_tica_rechazado",
                    correlacion_id=session.correlacion_id,
                    tipo_busqueda="dua",
                    numero_busqueda=session.dua.normalizado,
                    modalidad="terrestre",
                    estado="captcha_incorrecto",
                )
                # Un rechazo reutiliza exactamente el desafio ya mostrado en Dokka.
                return "captcha_incorrecto", session

            if session.expiry_task is not None:
                session.expiry_task.cancel()
                session.expiry_task = None
            session.processing_task = asyncio.create_task(
                self._procesar(session), name=f"process-terrestrial-{session.session_id}"
            )
            return "consultando", session
        except DuaNoEncontradoError:
            session.estado = EstadoSesionTerrestre.FALLIDO
            await self.cancelar(session_id)
            raise
        except BaseException as error:
            session.estado = EstadoSesionTerrestre.FALLIDO
            await self.cancelar(session_id)
            raise TerrestreError("Fallo la navegacion de la consulta terrestre.") from error

    async def estado(self, session_id: str) -> SesionTerrestre:
        return await self._obtener(session_id)

    async def _procesar(self, session: SesionTerrestre) -> None:
        try:
            async with asyncio.timeout(
                self.settings.terrestrial_processing_timeout_seconds
            ):
                raw = await extraer_resultado_terrestre(
                    session.page, session.dua
                )
                # El flujo cambia, pero el contrato y todas las reglas de
                # normalización son exactamente los de aéreo/marítimo.
                from app.models import ConsultaInput, Modalidad
                from app.orchestrator.consulta import ConsultaOrchestrator

                normalized = ConsultaOrchestrator.normalizar_resultado(
                    ConsultaInput(
                        manifiesto=session.dua.normalizado,
                        fecha_fin=date.today(),
                    ),
                    Modalidad.TERRESTRE,
                    raw,
                )
                session.resultado = normalized.model_dump(mode="json")
                session.resultado.update(
                    {
                        "dua": session.dua.normalizado,
                        "fecha_registro": normalized.momento3.fecha_dua.isoformat()
                        if normalized.momento3.fecha_dua
                        else "",
                    }
                )
            session.estado = EstadoSesionTerrestre.COMPLETADO
        except TimeoutError:
            session.error = "TICA excedio el tiempo maximo de procesamiento terrestre."
            session.estado = EstadoSesionTerrestre.FALLIDO
        except BaseException as error:
            session.error = str(error) or "Fallo la navegacion posterior al CAPTCHA."
            session.estado = EstadoSesionTerrestre.FALLIDO
        finally:
            self._logger.info(
                "consulta_tica_finalizada",
                correlacion_id=session.correlacion_id,
                tipo_busqueda="dua",
                numero_busqueda=session.dua.normalizado,
                modalidad="terrestre",
                estado=session.estado.value,
                duracion_ms=round((perf_counter() - session.iniciada_en) * 1_000, 2),
            )
            await self._cerrar_recursos(session)

    async def regenerar(self, session_id: str) -> SesionTerrestre:
        session = await self._obtener(session_id)
        async with self._navigation_lock:
            button = session.page.get_by_text("Generar otra imagen", exact=False)
            if await button.count() == 0:
                button = session.page.locator(
                    "input[value*='Generar otra'], button:has-text('Generar otra')"
                )
            if await button.count() == 0:
                raise TerrestreError("TICA no presento el control para generar otra imagen.")
            await button.first.click()
            await session.page.wait_for_timeout(300)
            session.captcha = await self._capturar_captcha(session.page)
        return session

    async def cancelar(self, session_id: str) -> None:
        async with self._registry_lock:
            session = self._sessions.pop(session_id, None)
        if session is None:
            return
        terminal_states = {
            EstadoSesionTerrestre.COMPLETADO,
            EstadoSesionTerrestre.FALLIDO,
            EstadoSesionTerrestre.EXPIRADO,
            EstadoSesionTerrestre.CANCELADO,
        }
        if session.estado not in terminal_states:
            session.estado = EstadoSesionTerrestre.CANCELADO
        if session.expiry_task is not None and session.expiry_task is not asyncio.current_task():
            session.expiry_task.cancel()
        if session.processing_task is not None and not session.processing_task.done():
            session.processing_task.cancel()
        await self._cerrar_recursos(session)

    async def completar(self, session_id: str) -> None:
        await self.cancelar(session_id)

    @staticmethod
    async def _cerrar_recursos(session: SesionTerrestre) -> None:
        for resource in (session.context, session.browser):
            try:
                await resource.close()
            except Exception:
                pass
        try:
            await session.playwright.stop()
        except Exception:
            pass

    async def _obtener(self, session_id: str) -> SesionTerrestre:
        await self._limpiar_expiradas()
        session = self._sessions.get(session_id)
        if session is None:
            raise SesionNoEncontradaError("La consulta terrestre no existe o ya expiro.")
        return session

    async def _limpiar_expiradas(self) -> None:
        now = datetime.now(UTC)
        expired = [key for key, value in self._sessions.items() if value.expires_at <= now]
        for key in expired:
            session = self._sessions.get(key)
            if session is not None:
                session.estado = EstadoSesionTerrestre.EXPIRADO
            await self.cancelar(key)

    async def _expire_after(self, session_id: str) -> None:
        try:
            await asyncio.sleep(self.settings.terrestrial_session_ttl_seconds)
            session = self._sessions.get(session_id)
            if session is None:
                return
            session.estado = EstadoSesionTerrestre.EXPIRADO
            await self.cancelar(session_id)
        except asyncio.CancelledError:
            return

    @staticmethod
    async def _capturar_captcha(page: Page) -> bytes:
        locator = page.locator("#captchaImage img")
        await locator.wait_for(state="visible")
        return await locator.screenshot()

    @staticmethod
    async def _esperar_resultado_captcha(page: Page) -> bool:
        """Espera la redireccion real; TICA puede tardar varios segundos en responder."""

        deadline = asyncio.get_running_loop().time() + 15
        while asyncio.get_running_loop().time() < deadline:
            if es_detalle_dua_url(page.url):
                return True
            await page.wait_for_timeout(100)
        return es_detalle_dua_url(page.url)


def extraer_fecha_registro(text: str) -> date | None:
    match = DATE_PATTERN.search(text)
    if match is None:
        return None
    year, month, day = (int(value) for value in match.groups())
    return date(year, month, day)


def es_detalle_dua_url(url: str) -> bool:
    """Reconoce el detalle aunque GeneXus agregue parametros a la URL."""

    return urlparse(url).path.lower().endswith(DETAIL_PATH)


def captcha_data_url(content: bytes) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:image/png;base64,{encoded}"


async def extraer_resultado_terrestre(page: Page, dua: PartesDua) -> dict[str, object]:
    """Normaliza el detalle DUA y sus movimientos al contrato de tres momentos."""

    texto_detalle = await page.locator("body").inner_text(timeout=5_000)
    fecha = extraer_fecha_registro(texto_detalle)
    if fecha is None:
        raise DuaNoEncontradoError("TICA no entrego la Fecha de Registro esperada.")
    totales = extraer_totales_dua_anticipado(texto_detalle)
    transportista = _extraer(texto_detalle, r"Empresa Transportista\s*(?:[A-Z]-)?[0-9]*\s*([^\n]+)")
    fecha_arribo = _extraer(texto_detalle, r"Fecha (?:de )?Arribo:\s*([0-9/]+)")

    boton = page.locator("input[name='AER'], input[value='Manifiesto/Stock']")
    movimientos: list[dict[str, str]] = []
    if await boton.count():
        await boton.first.click(timeout=10_000)
        await page.wait_for_load_state("domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(1_000)
        movimientos = await _recorrer_movimientos(page)

    momento2: dict[str, object] = {"movimientos": movimientos}
    if len(movimientos) == 1:
        momento2.update(movimientos[0])
    # Los totales del DUA son inequívocos incluso con varias líneas/movimientos.
    if totales.get("bultos"):
        momento2["bultos"] = totales["bultos"]
    if totales.get("peso_bruto"):
        momento2["peso_bruto"] = totales["peso_bruto"]

    valores: dict[str, object] = {
        "fecha_arribo": fecha_arribo,
        "transportista": transportista,
        **momento2,
        "dua_nacionalizacion": dua.normalizado,
        "fecha_dua": fecha.isoformat(),
    }
    return {
        "estado": "ok",
        "motivo": None,
        "valores": valores,
    }


async def _recorrer_movimientos(page: Page) -> list[dict[str, str]]:
    """Recorre páginas de líneas/afectaciones hasta encontrar movimientos ING."""

    pendientes = [page.url]
    visitadas: set[str] = set()
    encontrados: dict[str, dict[str, str]] = {}
    while pendientes and len(visitadas) < 30:
        url = pendientes.pop(0)
        if url in visitadas:
            continue
        visitadas.add(url)
        if page.url != url:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(500)
        filas = await _filas_estables(page)
        candidatos = movimientos_terrestres_desde_filas(filas)
        # Conserva compatibilidad si TICA entrega directamente la tabla aérea.
        if not candidatos:
            candidatos = [
                MovimientoTerrestre(
                    movimiento=item.movimiento,
                    almacen_fiscal=item.deposito,
                    movimiento_url=item.movimiento_url,
                    detenciones_url="",
                )
                for item in movimientos_desde_filas(filas)
            ]
        for movimiento in candidatos:
            if not movimiento.movimiento or movimiento.movimiento in encontrados:
                continue
            datos = {
                "movimiento_inventario": movimiento.movimiento,
                "almacen_fiscal": movimiento.almacen_fiscal,
            }
            detenciones = movimiento.detenciones_url
            if movimiento.movimiento_url:
                await page.goto(
                    movimiento.movimiento_url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                texto = await page.locator("body").inner_text(timeout=5_000)
                datos["almacen_fiscal"] = extraer_deposito(texto)
                detenciones = detenciones or await _enlace_con(page, "hskdetent.aspx")
            if detenciones:
                await page.goto(
                    detenciones, wait_until="domcontentloaded", timeout=30_000
                )
                texto_detenciones = await page.locator("body").inner_text(timeout=5_000)
                datos.update(extraer_detenciones(texto_detenciones))
            encontrados[movimiento.movimiento] = datos
        # GeneXus expone las siguientes pantallas como enlaces por fila.
        for fila in filas:
            enlaces = fila.get("enlaces")
            if not isinstance(enlaces, list):
                continue
            for enlace in enlaces:
                value = str(enlace)
                if any(
                    path in value.lower()
                    for path in (
                        "hcglineas.aspx",
                        "hcgafeli.aspx",
                        "hskmovstk.aspx",
                    )
                ):
                    pendientes.append(value)
    return list(encontrados.values())


def movimientos_terrestres_desde_filas(
    filas: list[dict[str, object]],
) -> list[MovimientoTerrestre]:
    """Reconoce movimientos por sus enlaces, sin imponer columnas aéreas."""

    resultado: list[MovimientoTerrestre] = []
    for fila in filas:
        cells_raw = fila.get("celdas")
        links_raw = fila.get("enlaces")
        if not isinstance(cells_raw, list) or not isinstance(links_raw, list):
            continue
        celdas = [" ".join(str(value).split()) for value in cells_raw]
        enlaces = [str(value) for value in links_raw]
        movimiento_url = next(
            (value for value in enlaces if "hskmov.aspx" in value.lower()), ""
        )
        detenciones_url = next(
            (value for value in enlaces if "hskdetent.aspx" in value.lower()), ""
        )
        if not movimiento_url and not detenciones_url:
            continue
        numeros = [value for value in celdas if re.fullmatch(r"\d{4,}", value)]
        movimiento = next(
            (value for value in numeros if not re.fullmatch(r"20\d{2}", value)), ""
        )
        if not movimiento:
            continue
        indice_deposito = next(
            (
                index
                for index, value in enumerate(celdas)
                if re.fullmatch(r"[A-Z][0-9]{3}", value)
            ),
            -1,
        )
        almacen = ""
        if indice_deposito >= 0:
            descripcion = (
                celdas[indice_deposito + 1]
                if indice_deposito + 1 < len(celdas)
                else ""
            )
            almacen = " ".join(
                value for value in (celdas[indice_deposito], descripcion) if value
            )
        resultado.append(
            MovimientoTerrestre(
                movimiento=movimiento,
                almacen_fiscal=almacen,
                movimiento_url=movimiento_url,
                detenciones_url=detenciones_url,
            )
        )
    return resultado


async def _enlace_con(page: Page, fragmento: str) -> str:
    for intento in range(3):
        try:
            value = await page.locator("a[href]").evaluate_all(
                """(links, part) => links.map(a => a.href)
                    .find(h => h.toLowerCase().includes(part)) || ''""",
                fragmento.lower(),
            )
            return str(value)
        except PlaywrightError as error:
            if "Execution context was destroyed" not in str(error) or intento == 2:
                raise
            await _esperar_navegacion_estable(page)
    return ""


async def _filas_estables(page: Page) -> list[dict[str, object]]:
    """Tolera las redirecciones automáticas de GeneXus mientras arma la tabla."""

    for intento in range(3):
        try:
            return await filas_con_enlaces(page)
        except PlaywrightError as error:
            if "Execution context was destroyed" not in str(error) or intento == 2:
                raise
            await _esperar_navegacion_estable(page)
    return []


async def _esperar_navegacion_estable(page: Page) -> None:
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=10_000)
    except PlaywrightError:
        pass
    await page.wait_for_timeout(500)


def _extraer(texto: str, patron: str) -> str:
    match = re.search(patron, texto, flags=re.IGNORECASE)
    return " ".join(match.group(1).split()) if match else ""
