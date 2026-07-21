"""Rutas HTTP del microservicio TICA."""

from datetime import datetime
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from pydantic import BaseModel, ConfigDict

from app.config import Settings, get_settings
from app.models import ConsultaLoteInput, ConsultaLoteResultado
from app.orchestrator import ConsultaLoteOrchestrator, ConsultaOrchestrator
from app.scraper.browser import BrowserManager, BrowserUnavailableError
from app.scraper.terrestre import (
    DuaInvalidoError,
    DuaNoEncontradoError,
    LimiteSesionesError,
    SesionNoEncontradaError,
    SesionTerrestre,
    TerrestreError,
    TerrestreSessionManager,
    captcha_data_url,
)

router = APIRouter()


class HealthResponse(BaseModel):
    """Respuesta pequena y estable para verificaciones de salud."""

    status: Literal["ok", "unavailable"]
    component: Literal["service", "portal"]


class TerrestreInicioInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    dua: str


class TerrestreCaptchaInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    captcha: str


class TerrestreChallengeResponse(BaseModel):
    estado: Literal["esperando_captcha", "captcha_incorrecto"]
    session_id: str
    dua: str
    captcha_image: str
    expires_at: datetime


class TerrestreProcesandoResponse(BaseModel):
    estado: Literal["consultando"]
    session_id: str
    dua: str


class TerrestreResultadoResponse(BaseModel):
    estado: Literal["ok", "completado"]
    dua: str
    fecha_registro: str
    motivo: str | None = None
    modalidad: Literal["terrestre"] = "terrestre"
    momento1: dict[str, object]
    momento2: dict[str, object]
    momento3: dict[str, object]


class TerrestreFalloResponse(BaseModel):
    estado: Literal["fallido"]
    detalle: str


class PortalHealthChecker:
    """Comprueba conectividad con TICA sin ejecutar una consulta de manifiesto."""

    def __init__(
        self,
        settings: Settings | None = None,
        browser: BrowserManager | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._browser = browser or BrowserManager(self._settings)

    async def disponible(self) -> bool:
        """Devuelve si la pagina inicial de TICA responde correctamente."""

        try:
            async with self._browser.pagina() as page:
                response = await page.goto(
                    self._settings.base_url,
                    wait_until="domcontentloaded",
                    timeout=self._settings.browser_timeout_ms,
                )
                return response is not None and response.ok
        except (
            BrowserUnavailableError,
            PlaywrightTimeoutError,
            PlaywrightError,
            OSError,
        ):
            return False


@lru_cache
def get_orchestrator() -> ConsultaOrchestrator:
    """Mantiene cache y dependencias compartidas entre solicitudes."""

    return ConsultaOrchestrator()


@lru_cache
def get_lote_orchestrator() -> ConsultaLoteOrchestrator:
    """Comparte el orquestador, navegador y cache entre todos los lotes."""

    return ConsultaLoteOrchestrator(get_orchestrator())


@lru_cache
def get_portal_health_checker() -> PortalHealthChecker:
    """Reutiliza la comprobacion configurada del portal."""

    return PortalHealthChecker()


@lru_cache
def get_terrestre_manager() -> TerrestreSessionManager:
    return TerrestreSessionManager()


def terrestrial_http_error(error: TerrestreError) -> HTTPException:
    code = 502
    if isinstance(error, DuaInvalidoError):
        code = 422
    elif isinstance(error, SesionNoEncontradaError):
        code = 410
    elif isinstance(error, LimiteSesionesError):
        code = 429
    elif isinstance(error, DuaNoEncontradoError):
        code = 404
    return HTTPException(status_code=code, detail=str(error))


def challenge_response(
    session: SesionTerrestre,
    estado: Literal["esperando_captcha", "captcha_incorrecto"] = "esperando_captcha",
) -> TerrestreChallengeResponse:
    return TerrestreChallengeResponse(
        estado=estado,
        session_id=session.session_id,
        dua=session.dua.normalizado,
        captcha_image=captcha_data_url(session.captcha),
        expires_at=session.expires_at,
    )


@router.post("/consultas-terrestres", response_model=TerrestreChallengeResponse)
async def iniciar_consulta_terrestre(
    entrada: TerrestreInicioInput,
    manager: Annotated[TerrestreSessionManager, Depends(get_terrestre_manager)],
) -> TerrestreChallengeResponse:
    try:
        return challenge_response(await manager.iniciar(entrada.dua))
    except TerrestreError as error:
        raise terrestrial_http_error(error) from error


@router.post(
    "/consultas-terrestres/{session_id}/resolver",
    response_model=TerrestreChallengeResponse | TerrestreProcesandoResponse,
)
async def resolver_consulta_terrestre(
    session_id: str,
    entrada: TerrestreCaptchaInput,
    manager: Annotated[TerrestreSessionManager, Depends(get_terrestre_manager)],
) -> TerrestreChallengeResponse | TerrestreProcesandoResponse:
    if not entrada.captcha.strip():
        raise HTTPException(status_code=422, detail="Debe ingresar el texto del CAPTCHA.")
    try:
        result, session = await manager.resolver(session_id, entrada.captcha)
        if result == "captcha_incorrecto":
            return challenge_response(session, "captcha_incorrecto")
        return TerrestreProcesandoResponse(
            estado="consultando", session_id=session.session_id, dua=session.dua.normalizado
        )
    except TerrestreError as error:
        raise terrestrial_http_error(error) from error


@router.get(
    "/consultas-terrestres/{session_id}",
    response_model=(
        TerrestreProcesandoResponse | TerrestreResultadoResponse | TerrestreFalloResponse
    ),
)
async def estado_consulta_terrestre(
    session_id: str,
    manager: Annotated[TerrestreSessionManager, Depends(get_terrestre_manager)],
) -> TerrestreProcesandoResponse | TerrestreResultadoResponse | TerrestreFalloResponse:
    try:
        session = await manager.estado(session_id)
        if session.estado.value == "completado" and session.resultado is not None:
            payload = dict(session.resultado)
            payload["estado"] = "completado"
            return TerrestreResultadoResponse.model_validate(payload)
        if session.estado.value == "fallido":
            return TerrestreFalloResponse(
                estado="fallido",
                detalle=session.error or "No fue posible completar la consulta terrestre.",
            )
        return TerrestreProcesandoResponse(
            estado="consultando", session_id=session.session_id, dua=session.dua.normalizado
        )
    except TerrestreError as error:
        raise terrestrial_http_error(error) from error


@router.post(
    "/consultas-terrestres/{session_id}/regenerar",
    response_model=TerrestreChallengeResponse,
)
async def regenerar_captcha_terrestre(
    session_id: str,
    manager: Annotated[TerrestreSessionManager, Depends(get_terrestre_manager)],
) -> TerrestreChallengeResponse:
    try:
        return challenge_response(await manager.regenerar(session_id))
    except TerrestreError as error:
        raise terrestrial_http_error(error) from error


@router.delete("/consultas-terrestres/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancelar_consulta_terrestre(
    session_id: str,
    manager: Annotated[TerrestreSessionManager, Depends(get_terrestre_manager)],
) -> Response:
    await manager.cancelar(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/consultas", response_model=ConsultaLoteResultado)
async def consultar_tica(
    entrada: ConsultaLoteInput,
    orchestrator: Annotated[
        ConsultaLoteOrchestrator,
        Depends(get_lote_orchestrator),
    ],
) -> ConsultaLoteResultado:
    """Valida y procesa uno o varios manifiestos en orden secuencial."""

    return await orchestrator.consultar(entrada)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Confirma que el proceso FastAPI esta disponible."""

    return HealthResponse(status="ok", component="service")


@router.get(
    "/health/portal",
    response_model=HealthResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": HealthResponse,
            "description": "Portal TICA no disponible",
        }
    },
)
async def health_portal(
    response: Response,
    checker: Annotated[PortalHealthChecker, Depends(get_portal_health_checker)],
) -> HealthResponse:
    """Comprueba TICA y responde 503 si el portal no esta disponible."""

    if await checker.disponible():
        return HealthResponse(status="ok", component="portal")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="unavailable", component="portal")
