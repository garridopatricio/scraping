"""Cache de ultima lectura buena para resultados TICA."""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from app.config import Settings, get_settings
from app.models import EstadoConsulta, Modalidad, ResultadoTICA


@dataclass(frozen=True, slots=True)
class CacheKey:
    """Identifica un resultado por modalidad detectada y manifiesto."""

    modalidad: Modalidad
    identificador: str


@dataclass(slots=True)
class _CacheEntry:
    result: ResultadoTICA
    expires_at: float


class ResultCache(Protocol):
    """Contrato desacoplado para permitir una implementacion futura en Redis."""

    async def guardar(self, result: ResultadoTICA) -> bool:
        """Guarda una lectura buena y devuelve si fue aceptada."""

    async def obtener(
        self,
        modalidad: Modalidad,
        identificador: str,
    ) -> ResultadoTICA | None:
        """Obtiene una copia vigente del ultimo resultado bueno."""

    async def eliminar(self, modalidad: Modalidad, identificador: str) -> bool:
        """Elimina una entrada y devuelve si existia."""


class InMemoryResultCache:
    """Almacenamiento en memoria protegido para uso asincrono."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        config = settings or get_settings()
        self._ttl_seconds = float(config.cache_ttl_seconds)
        self._clock = clock
        self._entries: dict[CacheKey, _CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def guardar(self, result: ResultadoTICA) -> bool:
        """Guarda solo resultados ``ok`` para no convertir fallos en lecturas buenas."""

        if result.estado is not EstadoConsulta.OK or result.modalidad is None:
            return False

        key = self._key(result.modalidad, result.identificador)
        entry = _CacheEntry(
            result=result.model_copy(deep=True),
            expires_at=self._clock() + self._ttl_seconds,
        )
        async with self._lock:
            self._entries[key] = entry
        return True

    async def obtener(
        self,
        modalidad: Modalidad,
        identificador: str,
    ) -> ResultadoTICA | None:
        """Devuelve una copia del resultado o ``None`` si no existe/expiró."""

        key = self._key(modalidad, identificador)
        async with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at <= self._clock():
                del self._entries[key]
                return None
            return entry.result.model_copy(deep=True)

    async def eliminar(self, modalidad: Modalidad, identificador: str) -> bool:
        """Elimina una lectura concreta."""

        key = self._key(modalidad, identificador)
        async with self._lock:
            return self._entries.pop(key, None) is not None

    async def limpiar(self) -> None:
        """Elimina todas las lecturas almacenadas."""

        async with self._lock:
            self._entries.clear()

    async def limpiar_expirados(self) -> int:
        """Elimina entradas vencidas y devuelve la cantidad retirada."""

        now = self._clock()
        async with self._lock:
            expired = [key for key, entry in self._entries.items() if entry.expires_at <= now]
            for key in expired:
                del self._entries[key]
            return len(expired)

    async def cantidad(self) -> int:
        """Devuelve la cantidad de entradas, util para observabilidad y pruebas."""

        async with self._lock:
            return len(self._entries)

    @staticmethod
    def _key(modalidad: Modalidad, identificador: str) -> CacheKey:
        return CacheKey(modalidad=modalidad, identificador=identificador.strip())
