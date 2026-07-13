"""Pruebas del logging estructurado y su integracion."""

import json
from typing import cast

import structlog
from pytest import CaptureFixture

from app.config import Settings
from app.models import EstadoConsulta, Modalidad, ResultadoTICA
from app.observability.logging import (
    EventLogger,
    configurar_logging,
    obtener_logger,
    registrar_consulta,
)


class MemoryLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def info(self, event: str, **values: object) -> object:
        self.events.append((event, values))
        return None

    def exception(self, event: str, **values: object) -> object:
        self.events.append((event, values))
        return None


def test_registra_estado_modalidad_duracion_y_correlacion_sin_manifiesto() -> None:
    logger = MemoryLogger()
    result = ResultadoTICA(
        estado=EstadoConsulta.OK,
        modalidad=Modalidad.MARITIMO,
        identificador="MANIFIESTO-SENSIBLE",
    )

    registrar_consulta(
        cast(EventLogger, logger),
        resultado=result,
        duracion_ms=12.345,
        correlacion_id="corr-123",
    )

    event, values = logger.events[0]
    assert event == "consulta_tica_finalizada"
    assert values == {
        "correlacion_id": "corr-123",
        "modalidad": "maritimo",
        "estado": "ok",
        "duracion_ms": 12.35,
    }
    assert "MANIFIESTO-SENSIBLE" not in str(logger.events)


def test_configuracion_emite_una_linea_json(capsys: CaptureFixture[str]) -> None:
    structlog.reset_defaults()
    configurar_logging(Settings(app_env="test", log_level="INFO"))
    logger = obtener_logger("test")

    registrar_consulta(
        logger,
        resultado=ResultadoTICA(
            estado=EstadoConsulta.PENDING,
            modalidad=Modalidad.AEREO,
            identificador="NO-DEBE-APARECER",
        ),
        duracion_ms=7.0,
        correlacion_id="corr-json",
    )

    output = json.loads(capsys.readouterr().out)
    assert output["event"] == "consulta_tica_finalizada"
    assert output["estado"] == "pending"
    assert output["modalidad"] == "aereo"
    assert output["duracion_ms"] == 7.0
    assert output["correlacion_id"] == "corr-json"
    assert "NO-DEBE-APARECER" not in output.values()
