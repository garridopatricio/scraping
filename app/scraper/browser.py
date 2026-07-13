"""Gestion segura y serializada del navegador Playwright."""

import asyncio
import sys
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from dataclasses import dataclass

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from playwright.async_api import (
    Error as PlaywrightError,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from app.config import Settings, get_settings
from app.scraper.captcha import CaptchaRequiredError, contiene_captcha


class BrowserUnavailableError(RuntimeError):
    """Indica que no fue posible iniciar Chromium despues de los reintentos."""

    def __init__(self, attempts: int, reason: str) -> None:
        self.attempts = attempts
        self.reason = reason
        super().__init__(f"navegador no disponible tras {attempts} intentos: {reason}")


@dataclass(slots=True)
class _BrowserResources:
    """Recursos abiertos que deben cerrarse al finalizar la consulta."""

    stack: AsyncExitStack
    page: Page


PlaywrightFactory = Callable[[], AbstractAsyncContextManager[Playwright]]
SleepFunction = Callable[[float], Awaitable[None]]


class BrowserManager:
    """Entrega paginas Playwright con apertura serializada y reintentos.

    ``browser_max_retries`` representa reintentos adicionales despues del primer
    intento. La cerradura compartida evita abrir mas de una sesion simultanea
    contra TICA dentro del proceso.
    """

    _serial_lock = asyncio.Lock()

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        playwright_factory: PlaywrightFactory = async_playwright,
        sleep: SleepFunction = asyncio.sleep,
    ) -> None:
        self.settings = settings or get_settings()
        self._playwright_factory = playwright_factory
        self._sleep = sleep

    @asynccontextmanager
    async def pagina(self) -> AsyncIterator[Page]:
        """Abre una pagina exclusiva y garantiza el cierre de sus recursos."""

        self._asegurar_event_loop_compatible()
        async with self._serial_lock:
            resources = await self._iniciar_con_reintentos()
            try:
                yield resources.page
            finally:
                await resources.stack.aclose()

    @staticmethod
    def _asegurar_event_loop_compatible() -> None:
        """Evita iniciar Playwright con el loop selector incompatible de Windows."""

        loop = asyncio.get_running_loop()
        if sys.platform == "win32" and isinstance(loop, asyncio.SelectorEventLoop):
            raise BrowserUnavailableError(
                attempts=0,
                reason=(
                    "el event loop selector de Windows no permite iniciar Playwright; "
                    "ejecute Uvicorn sin --reload"
                ),
            )

    async def asegurar_sin_captcha(self, page: Page) -> None:
        """Detiene el flujo si la pagina visible contiene un CAPTCHA."""

        text = await page.locator("body").inner_text()
        if contiene_captcha(text):
            raise CaptchaRequiredError("TICA requiere CAPTCHA; no se intentara resolverlo")

    async def _iniciar_con_reintentos(self) -> _BrowserResources:
        attempts = self.settings.browser_max_retries + 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                return await self._iniciar_una_vez()
            except NotImplementedError as error:
                raise BrowserUnavailableError(
                    attempts=attempt,
                    reason=(
                        "el event loop de Windows no permite iniciar Playwright; "
                        "ejecute Uvicorn sin --reload"
                    ),
                ) from error
            except (PlaywrightTimeoutError, PlaywrightError, OSError) as error:
                last_error = error
                if attempt == attempts:
                    break
                delay = self.settings.browser_backoff_seconds * (2 ** (attempt - 1))
                await self._sleep(delay)

        reason = str(last_error) if last_error else "error desconocido"
        raise BrowserUnavailableError(attempts=attempts, reason=reason) from last_error

    async def _iniciar_una_vez(self) -> _BrowserResources:
        stack = AsyncExitStack()
        try:
            playwright = await stack.enter_async_context(self._playwright_factory())
            browser: Browser = await playwright.chromium.launch(
                headless=self.settings.browser_headless
            )
            stack.push_async_callback(browser.close)

            context: BrowserContext = await browser.new_context(
                viewport={"width": 1440, "height": 1000}
            )
            stack.push_async_callback(context.close)

            page = await context.new_page()
            page.set_default_timeout(self.settings.browser_timeout_ms)
            return _BrowserResources(stack=stack, page=page)
        except BaseException:
            await stack.aclose()
            raise
