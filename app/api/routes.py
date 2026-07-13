"""Rutas HTTP del microservicio TICA."""

from functools import lru_cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.models import ConsultaInput, ResultadoTICA
from app.orchestrator import ConsultaOrchestrator
from app.scraper.browser import BrowserManager, BrowserUnavailableError

router = APIRouter()


class HealthResponse(BaseModel):
    """Respuesta pequena y estable para verificaciones de salud."""

    status: Literal["ok", "unavailable"]
    component: Literal["service", "portal"]


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
def get_portal_health_checker() -> PortalHealthChecker:
    """Reutiliza la comprobacion configurada del portal."""

    return PortalHealthChecker()


@router.post("/consultas", response_model=ResultadoTICA)
async def consultar_tica(
    entrada: ConsultaInput,
    orchestrator: Annotated[ConsultaOrchestrator, Depends(get_orchestrator)],
) -> ResultadoTICA:
    """Valida la entrada y delega la consulta al orquestador."""

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
