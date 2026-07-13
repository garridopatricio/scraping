"""Orquestacion central de una consulta TICA."""

from __future__ import annotations

import re
from contextlib import AbstractAsyncContextManager
from datetime import date, datetime, timedelta
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.cache import InMemoryResultCache, ResultCache
from app.models import (
    ConsultaInput,
    DatosMomento1,
    DatosMomento2,
    DatosMomento3,
    EstadoConsulta,
    Modalidad,
    ResultadoTICA,
)
from app.observability.logging import (
    EventLogger,
    obtener_logger,
    registrar_consulta,
    registrar_error_inesperado,
)
from app.scraper.base import FlujoNoMigradoError, ResultadoEstrategia, fecha_para_tica
from app.scraper.browser import BrowserManager, BrowserUnavailableError
from app.scraper.captcha import CaptchaRequiredError
from app.scraper.dispatcher import DespachadorEstrategias, ModalidadNoDeterminadaError
from app.scraper.domain import BusquedaConocimiento
from app.scraper.portal import buscar_conocimiento


class BrowserGateway(Protocol):
    """Operaciones del navegador requeridas por el orquestador."""

    def pagina(self) -> AbstractAsyncContextManager[Page]: ...

    async def asegurar_sin_captcha(self, page: Page) -> None: ...


class SearchKnowledge(Protocol):
    """Firma de la busqueda inicial ya implementada en la PoC."""

    async def __call__(
        self,
        page: Page,
        numero: str,
        fecha_fin: str,
        evidencia_prefijo: str,
        fecha_inicio: str | None = None,
    ) -> BusquedaConocimiento: ...


class StrategyDispatcher(Protocol):
    """Despacho minimo requerido por el orquestador."""

    async def consultar(
        self,
        page: Page,
        entrada: ConsultaInput,
        busqueda: BusquedaConocimiento,
    ) -> ResultadoEstrategia: ...


class ConsultaOrchestrator:
    """Coordina navegador, clasificacion, estrategias, estados y cache."""

    def __init__(
        self,
        *,
        browser: BrowserGateway | None = None,
        cache: ResultCache | None = None,
        dispatcher: StrategyDispatcher | None = None,
        search: SearchKnowledge = buscar_conocimiento,
        logger: EventLogger | None = None,
    ) -> None:
        self._browser = browser or BrowserManager()
        self._cache = cache or InMemoryResultCache()
        self._dispatcher = dispatcher or DespachadorEstrategias()
        self._search = search
        self._logger = logger or obtener_logger(__name__)

    async def consultar(self, entrada: ConsultaInput) -> ResultadoTICA:
        """Ejecuta y registra una consulta sin exponer su manifiesto."""

        started_at = perf_counter()
        correlation_id = uuid4().hex
        try:
            result = await self._consultar(entrada)
        except Exception:
            registrar_error_inesperado(
                self._logger,
                duracion_ms=(perf_counter() - started_at) * 1_000,
                correlacion_id=correlation_id,
            )
            raise

        registrar_consulta(
            self._logger,
            resultado=result,
            duracion_ms=(perf_counter() - started_at) * 1_000,
            correlacion_id=correlation_id,
        )
        return result

    async def _consultar(self, entrada: ConsultaInput) -> ResultadoTICA:
        """Ejecuta una consulta completa y siempre devuelve un estado controlado."""

        detected: Modalidad | None = None
        try:
            async with self._browser.pagina() as page:
                search = await self._search(
                    page=page,
                    numero=entrada.manifiesto,
                    fecha_inicio=fecha_para_tica(self._fecha_inicio(entrada.fecha_fin)),
                    fecha_fin=fecha_para_tica(entrada.fecha_fin),
                    evidencia_prefijo="produccion_conocimiento",
                )
                await self._browser.asegurar_sin_captcha(page)

                if search.fila is None:
                    return self._simple_result(
                        entrada,
                        EstadoConsulta.NOT_FOUND,
                        reason="manifiesto_no_encontrado",
                    )

                try:
                    detected = Modalidad(search.modalidad_detectada)
                except ValueError:
                    return self._simple_result(
                        entrada,
                        EstadoConsulta.NEEDS_REVIEW,
                        reason=f"modalidad_no_determinada:{search.modalidad_detectada}",
                    )

                raw = await self._dispatcher.consultar(page, entrada, search)
                await self._browser.asegurar_sin_captcha(page)
                result = self._map_result(entrada, detected, raw)
                await self._cache.guardar(result)
                return result
        except CaptchaRequiredError:
            return await self._degraded(entrada, detected, "captcha_required")
        except BrowserUnavailableError:
            return await self._degraded(entrada, detected, "browser_unavailable")
        except (PlaywrightTimeoutError, PlaywrightError, OSError):
            return await self._degraded(entrada, detected, "portal_unavailable")
        except ModalidadNoDeterminadaError:
            return self._simple_result(
                entrada,
                EstadoConsulta.NEEDS_REVIEW,
                modalidad=detected,
                reason="modalidad_no_soportada",
            )
        except FlujoNoMigradoError:
            return self._simple_result(
                entrada,
                EstadoConsulta.NOT_IMPLEMENTED,
                modalidad=detected,
                reason="flujo_modalidad_pendiente_de_migracion",
            )
        except RuntimeError as error:
            reason = "captcha_required" if "captcha" in str(error).lower() else "consulta_error"
            return await self._degraded(entrada, detected, reason)

    async def _degraded(
        self,
        entrada: ConsultaInput,
        modalidad: Modalidad | None,
        reason: str,
    ) -> ResultadoTICA:
        cached = await self._last_good(modalidad, entrada.manifiesto)
        if cached is None:
            return self._simple_result(
                entrada,
                EstadoConsulta.UNAVAILABLE,
                modalidad=modalidad,
                reason=reason,
            )

        stale = cached.model_copy(deep=True)
        stale.estado = EstadoConsulta.STALE
        stale.desde_cache = True
        stale.motivo = reason
        return stale

    async def _last_good(
        self,
        modalidad: Modalidad | None,
        identificador: str,
    ) -> ResultadoTICA | None:
        modalities = (modalidad,) if modalidad else tuple(Modalidad)
        candidates = [
            cached
            for item in modalities
            if (cached := await self._cache.obtener(item, identificador)) is not None
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda result: result.consultado_en)

    @staticmethod
    def _fecha_inicio(fecha_fin: date) -> date:
        """Incluye fecha fin y limita la ventana total a 15 dias."""

        return fecha_fin - timedelta(days=14)

    @classmethod
    def _map_result(
        cls,
        entrada: ConsultaInput,
        modalidad: Modalidad,
        raw: ResultadoEstrategia,
    ) -> ResultadoTICA:
        values = cls._values(raw)
        raw_status = str(raw.get("estado", ""))
        dua = values.get("dua_nacionalizacion", "")

        if raw_status == "no_encontrado":
            status = EstadoConsulta.NOT_FOUND
        elif raw_status == "modalidad_no_corresponde":
            status = EstadoConsulta.NEEDS_REVIEW
        elif raw_status == "sin_arribo" or not dua:
            status = EstadoConsulta.PENDING
        else:
            status = EstadoConsulta.OK

        return ResultadoTICA(
            estado=status,
            modalidad=modalidad,
            identificador=entrada.manifiesto,
            momento1=DatosMomento1(
                fecha_arribo=cls._parse_date(values.get("fecha_arribo")),
                transportista=cls._text_or_none(values.get("transportista")),
            ),
            momento2=DatosMomento2(
                movimiento_inventario=cls._text_or_none(
                    values.get("movimiento_inventario")
                ),
                almacen_fiscal=cls._text_or_none(values.get("almacen_fiscal")),
                fecha_ingreso_regimen=cls._parse_date(values.get("fecha_ingreso_regimen")),
                fecha_movimiento_inventario=cls._parse_datetime(
                    values.get("fecha_movimiento_inventario")
                ),
                bultos=cls._parse_integer(values.get("bultos")),
                peso_bruto=cls._parse_integer(values.get("peso_bruto")),
            ),
            momento3=DatosMomento3(
                dua_nacionalizacion=cls._text_or_none(dua),
                fecha_dua=cls._parse_date(values.get("fecha_dua")),
            ),
            motivo=cls._reason(raw),
        )

    @staticmethod
    def _simple_result(
        entrada: ConsultaInput,
        status: EstadoConsulta,
        *,
        modalidad: Modalidad | None = None,
        reason: str,
    ) -> ResultadoTICA:
        return ResultadoTICA(
            estado=status,
            modalidad=modalidad,
            identificador=entrada.manifiesto,
            motivo=reason,
        )

    @staticmethod
    def _values(raw: ResultadoEstrategia) -> dict[str, str]:
        values = raw.get("valores")
        if not isinstance(values, dict):
            return {}
        return {
            str(key): str(value).strip()
            for key, value in values.items()
            if value is not None
        }

    @staticmethod
    def _reason(raw: ResultadoEstrategia) -> str | None:
        observations = raw.get("observaciones")
        if isinstance(observations, list):
            text = "; ".join(str(item) for item in observations if item)
            return text[:300] or None
        raw_status = str(raw.get("estado", "")).strip()
        return raw_status[:300] or None

    @staticmethod
    def _text_or_none(value: str | None) -> str | None:
        text = (value or "").strip()
        return text or None

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        text = (value or "").strip()
        for format_ in ("%d/%m/%y", "%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, format_).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        text = (value or "").strip()
        for format_ in ("%d/%m/%y %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(text, format_)
            except ValueError:
                continue
        parsed_date = ConsultaOrchestrator._parse_date(text)
        return datetime.combine(parsed_date, datetime.min.time()) if parsed_date else None

    @staticmethod
    def _parse_integer(value: str | None) -> int | None:
        """Convierte cantidades TICA; un punto separa miles, no decimales."""

        text = re.sub(r"[\s\u00a0]", "", (value or "").strip())
        if re.fullmatch(r"\d+", text):
            return int(text)
        if re.fullmatch(r"\d+(?:[.,]\d{3})+", text):
            return int(text.replace(".", "").replace(",", ""))
        return None
