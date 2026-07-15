"""Coordinacion secuencial de consultas TICA por lote."""

from typing import Protocol

from app.models import (
    ConsultaInput,
    ConsultaLoteInput,
    ConsultaLoteResultado,
    EstadoConsulta,
    ResultadoManifiesto,
    ResultadoTICA,
)
from app.orchestrator.consulta import ConsultaOrchestrator


class SingleConsulta(Protocol):
    """Operacion unitaria requerida por el coordinador de lotes."""

    async def consultar(self, entrada: ConsultaInput) -> ResultadoTICA: ...


class ConsultaLoteOrchestrator:
    """Procesa manifiestos en orden y aisla el resultado de cada uno."""

    def __init__(self, orchestrator: SingleConsulta | None = None) -> None:
        self._orchestrator = orchestrator or ConsultaOrchestrator()

    async def consultar(self, entrada: ConsultaLoteInput) -> ConsultaLoteResultado:
        """Consulta cada manifiesto secuencialmente y conserva el orden de entrada."""

        results: ConsultaLoteResultado = {}
        for manifest in entrada.manifiestos:
            try:
                result = await self._orchestrator.consultar(
                    ConsultaInput(
                        manifiesto=manifest,
                        fecha_inicio=entrada.fecha_inicio,
                        fecha_fin=entrada.fecha_fin,
                    )
                )
            except Exception:
                result = ResultadoTICA(
                    estado=EstadoConsulta.UNAVAILABLE,
                    identificador=manifest,
                    motivo="error_interno_manifiesto",
                )
            results[manifest] = ResultadoManifiesto.desde_resultado(result)

        return results
