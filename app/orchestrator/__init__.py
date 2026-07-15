"""Orquestacion de consultas por modalidad detectada."""

from app.orchestrator.consulta import ConsultaOrchestrator
from app.orchestrator.lote import ConsultaLoteOrchestrator

__all__ = ["ConsultaLoteOrchestrator", "ConsultaOrchestrator"]
