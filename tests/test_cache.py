"""Pruebas de la cache de ultima lectura buena."""

from dataclasses import dataclass

import pytest

from app.cache import InMemoryResultCache, ResultCache
from app.config import Settings
from app.models import EstadoConsulta, Modalidad, ResultadoTICA


@dataclass
class FakeClock:
    value: float = 1_000.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def crear_cache(clock: FakeClock, ttl: int = 60) -> InMemoryResultCache:
    settings = Settings(cache_ttl_seconds=ttl)
    cache: ResultCache = InMemoryResultCache(settings, clock=clock)
    assert isinstance(cache, InMemoryResultCache)
    return cache


def crear_resultado(
    *,
    estado: EstadoConsulta = EstadoConsulta.OK,
    modalidad: Modalidad = Modalidad.AEREO,
    identificador: str = "872219087246",
) -> ResultadoTICA:
    return ResultadoTICA(
        estado=estado,
        modalidad=modalidad,
        identificador=identificador,
    )


@pytest.mark.asyncio
async def test_guarda_y_recupera_ultima_lectura_buena() -> None:
    cache = crear_cache(FakeClock())
    result = crear_resultado()

    assert await cache.guardar(result) is True
    recovered = await cache.obtener(Modalidad.AEREO, "872219087246")

    assert recovered == result
    assert recovered is not result


@pytest.mark.asyncio
async def test_no_guarda_resultados_que_no_sean_ok() -> None:
    cache = crear_cache(FakeClock())

    for status in EstadoConsulta:
        if status is EstadoConsulta.OK:
            continue
        assert await cache.guardar(crear_resultado(estado=status)) is False

    assert await cache.cantidad() == 0


@pytest.mark.asyncio
async def test_resultado_expira_al_cumplir_ttl() -> None:
    clock = FakeClock()
    cache = crear_cache(clock, ttl=30)
    await cache.guardar(crear_resultado())

    clock.advance(29.9)
    assert await cache.obtener(Modalidad.AEREO, "872219087246") is not None

    clock.advance(0.1)
    assert await cache.obtener(Modalidad.AEREO, "872219087246") is None
    assert await cache.cantidad() == 0


@pytest.mark.asyncio
async def test_clave_separa_modalidad_e_identificador() -> None:
    cache = crear_cache(FakeClock())
    await cache.guardar(crear_resultado(modalidad=Modalidad.AEREO, identificador="MISMO"))
    await cache.guardar(crear_resultado(modalidad=Modalidad.MARITIMO, identificador="MISMO"))

    assert await cache.obtener(Modalidad.AEREO, "MISMO") is not None
    assert await cache.obtener(Modalidad.MARITIMO, "MISMO") is not None
    assert await cache.cantidad() == 2


@pytest.mark.asyncio
async def test_reemplazar_lectura_renueva_ttl_y_aísla_mutaciones() -> None:
    clock = FakeClock()
    cache = crear_cache(clock, ttl=10)
    result = crear_resultado()
    await cache.guardar(result)

    clock.advance(8)
    result.motivo = "cambio externo"
    await cache.guardar(crear_resultado())
    clock.advance(5)

    recovered = await cache.obtener(Modalidad.AEREO, "872219087246")
    assert recovered is not None
    assert recovered.motivo is None


@pytest.mark.asyncio
async def test_eliminar_limpiar_y_purgar_expirados() -> None:
    clock = FakeClock()
    cache = crear_cache(clock, ttl=5)
    await cache.guardar(crear_resultado(identificador="A"))
    await cache.guardar(crear_resultado(identificador="B"))

    assert await cache.eliminar(Modalidad.AEREO, "A") is True
    assert await cache.eliminar(Modalidad.AEREO, "A") is False

    clock.advance(5)
    assert await cache.limpiar_expirados() == 1
    assert await cache.cantidad() == 0

    await cache.guardar(crear_resultado(identificador="C"))
    await cache.limpiar()
    assert await cache.cantidad() == 0

