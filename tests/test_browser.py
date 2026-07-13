"""Pruebas del gestor serializado de Playwright."""

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from typing import cast

import pytest
from playwright.async_api import Page, Playwright

from app.config import Settings
from app.scraper.browser import (
    BrowserManager,
    BrowserUnavailableError,
    PlaywrightFactory,
)
from app.scraper.captcha import CaptchaRequiredError


class FakeLocator:
    def __init__(self, text: str) -> None:
        self.text = text

    async def inner_text(self) -> str:
        return self.text


class FakePage:
    def __init__(self, body_text: str = "Portal TICA") -> None:
        self.body_text = body_text
        self.default_timeout: float | None = None

    def set_default_timeout(self, timeout: float) -> None:
        self.default_timeout = timeout

    def locator(self, selector: str) -> FakeLocator:
        assert selector == "body"
        return FakeLocator(self.body_text)


class FakeContext:
    def __init__(self, state: "FakePlaywrightState") -> None:
        self.state = state
        self.page = FakePage()

    async def new_page(self) -> Page:
        return cast(Page, self.page)

    async def close(self) -> None:
        self.state.context_close_calls += 1


class FakeBrowser:
    def __init__(self, state: "FakePlaywrightState") -> None:
        self.state = state

    async def new_context(self, **options: object) -> FakeContext:
        self.state.viewport_options.append(options)
        return FakeContext(self.state)

    async def close(self) -> None:
        self.state.browser_close_calls += 1


class FakeChromium:
    def __init__(self, state: "FakePlaywrightState") -> None:
        self.state = state

    async def launch(self, *, headless: bool) -> FakeBrowser:
        self.state.launch_calls += 1
        self.state.headless_values.append(headless)
        if self.state.launch_calls <= self.state.fail_launches:
            raise OSError("Chromium no disponible")
        return FakeBrowser(self.state)


class FakePlaywright:
    def __init__(self, state: "FakePlaywrightState") -> None:
        self.chromium = FakeChromium(state)


class FakePlaywrightContext:
    def __init__(self, state: "FakePlaywrightState") -> None:
        self.state = state

    async def __aenter__(self) -> FakePlaywright:
        self.state.playwright_enter_calls += 1
        return FakePlaywright(self.state)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        self.state.playwright_exit_calls += 1


class FakePlaywrightState:
    def __init__(self, *, fail_launches: int = 0) -> None:
        self.fail_launches = fail_launches
        self.launch_calls = 0
        self.playwright_enter_calls = 0
        self.playwright_exit_calls = 0
        self.browser_close_calls = 0
        self.context_close_calls = 0
        self.headless_values: list[bool] = []
        self.viewport_options: list[dict[str, object]] = []

    def factory(self) -> AbstractAsyncContextManager[Playwright]:
        context = FakePlaywrightContext(self)
        return cast(AbstractAsyncContextManager[Playwright], context)


def crear_manager(
    state: FakePlaywrightState,
    *,
    retries: int = 2,
    backoff: float = 0.5,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> BrowserManager:
    settings = Settings(
        browser_headless=True,
        browser_timeout_ms=12_345,
        browser_max_retries=retries,
        browser_backoff_seconds=backoff,
    )
    factory: PlaywrightFactory = state.factory
    return BrowserManager(settings, playwright_factory=factory, sleep=sleep)


@pytest.mark.asyncio
async def test_pagina_configura_y_cierra_todos_los_recursos() -> None:
    state = FakePlaywrightState()
    manager = crear_manager(state)

    async with manager.pagina() as page:
        fake_page = cast(FakePage, page)
        assert fake_page.default_timeout == 12_345

    assert state.headless_values == [True]
    assert state.context_close_calls == 1
    assert state.browser_close_calls == 1
    assert state.playwright_exit_calls == 1


@pytest.mark.asyncio
async def test_inicio_reintenta_con_backoff_exponencial() -> None:
    state = FakePlaywrightState(fail_launches=2)
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    manager = crear_manager(state, retries=2, backoff=0.5, sleep=fake_sleep)

    async with manager.pagina():
        pass

    assert state.launch_calls == 3
    assert delays == [0.5, 1.0]
    assert state.playwright_exit_calls == 3


@pytest.mark.asyncio
async def test_inicio_agotado_devuelve_error_controlado() -> None:
    state = FakePlaywrightState(fail_launches=10)

    async def fake_sleep(_: float) -> None:
        return None

    manager = crear_manager(state, retries=2, sleep=fake_sleep)

    with pytest.raises(BrowserUnavailableError) as captured:
        async with manager.pagina():
            pass

    assert captured.value.attempts == 3
    assert captured.value.reason == "Chromium no disponible"
    assert state.launch_calls == 3


@pytest.mark.asyncio
async def test_event_loop_windows_incompatible_devuelve_error_controlado() -> None:
    class UnsupportedPlaywrightContext:
        async def __aenter__(self) -> Playwright:
            raise NotImplementedError

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: object,
        ) -> None:
            return None

    def unsupported_factory() -> AbstractAsyncContextManager[Playwright]:
        return UnsupportedPlaywrightContext()

    manager = BrowserManager(
        Settings(browser_max_retries=3),
        playwright_factory=unsupported_factory,
    )

    with pytest.raises(BrowserUnavailableError) as captured:
        async with manager.pagina():
            pass

    assert captured.value.attempts == 1
    assert "sin --reload" in captured.value.reason


@pytest.mark.asyncio
async def test_sesiones_concurrentes_se_ejecutan_en_serie() -> None:
    state = FakePlaywrightState()
    manager = crear_manager(state)
    first_entered = asyncio.Event()
    release_first = asyncio.Event()
    order: list[str] = []

    async def first() -> None:
        async with manager.pagina():
            order.append("first-enter")
            first_entered.set()
            await release_first.wait()
            order.append("first-exit")

    async def second() -> None:
        await first_entered.wait()
        async with manager.pagina():
            order.append("second-enter")

    first_task = asyncio.create_task(first())
    second_task = asyncio.create_task(second())
    await first_entered.wait()
    await asyncio.sleep(0)

    assert state.launch_calls == 1
    release_first.set()
    await asyncio.gather(first_task, second_task)

    assert order == ["first-enter", "first-exit", "second-enter"]
    assert state.launch_calls == 2


@pytest.mark.asyncio
async def test_captcha_detiene_el_flujo_sin_resolverlo() -> None:
    manager = crear_manager(FakePlaywrightState())
    page = cast(Page, FakePage("Complete el CAPTCHA para continuar"))

    with pytest.raises(CaptchaRequiredError, match="no se intentara resolverlo"):
        await manager.asegurar_sin_captcha(page)
