"""Pruebas del procesamiento secuencial por lote."""

import asyncio
from datetime import date

import pytest

from app.models import ConsultaInput, ConsultaLoteInput, EstadoConsulta, ResultadoTICA
from app.orchestrator.lote import ConsultaLoteOrchestrator


class RecordingOrchestrator:
    def __init__(self, fail_manifiesto: str | None = None) -> None:
        self.fail_manifiesto = fail_manifiesto
        self.calls: list[ConsultaInput] = []
        self.active = 0
        self.max_active = 0

    async def consultar(self, entrada: ConsultaInput) -> ResultadoTICA:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        self.calls.append(entrada)
        await asyncio.sleep(0)
        self.active -= 1
        if entrada.manifiesto == self.fail_manifiesto:
            raise RuntimeError("fallo aislado")
        return ResultadoTICA(
            estado=EstadoConsulta.NOT_IMPLEMENTED,
            identificador=entrada.manifiesto,
        )


@pytest.mark.asyncio
async def test_lote_ejecuta_secuencialmente_y_conserva_orden() -> None:
    single = RecordingOrchestrator()
    orchestrator = ConsultaLoteOrchestrator(single)

    result = await orchestrator.consultar(
        ConsultaLoteInput(
            manifiestos=["MANIFIESTO-A", "MANIFIESTO-B", "MANIFIESTO-C"],
            fecha_fin=date(2026, 7, 14),
        )
    )

    assert single.max_active == 1
    assert [call.manifiesto for call in single.calls] == [
        "MANIFIESTO-A",
        "MANIFIESTO-B",
        "MANIFIESTO-C",
    ]
    assert all(call.fecha_fin == date(2026, 7, 14) for call in single.calls)
    assert all(call.fecha_inicio is None for call in single.calls)
    assert list(result) == [
        "MANIFIESTO-A",
        "MANIFIESTO-B",
        "MANIFIESTO-C",
    ]


@pytest.mark.asyncio
async def test_fallo_de_un_manifiesto_no_interrumpe_los_siguientes() -> None:
    single = RecordingOrchestrator(fail_manifiesto="MANIFIESTO-B")
    orchestrator = ConsultaLoteOrchestrator(single)

    result = await orchestrator.consultar(
        ConsultaLoteInput(
            manifiestos=["MANIFIESTO-A", "MANIFIESTO-B", "MANIFIESTO-C"],
            fecha_fin=date(2026, 7, 14),
        )
    )

    assert [item.estado for item in result.values()] == [
        EstadoConsulta.NOT_IMPLEMENTED,
        EstadoConsulta.UNAVAILABLE,
        EstadoConsulta.NOT_IMPLEMENTED,
    ]
    assert result["MANIFIESTO-B"].motivo == "error_interno_manifiesto"
    assert len(single.calls) == 3


def test_lote_acepta_mas_de_diez_manifiestos() -> None:
    entrada = ConsultaLoteInput(
        manifiestos=[f"MANIFIESTO-{index}" for index in range(11)],
        fecha_fin=date(2026, 7, 14),
    )

    assert len(entrada.manifiestos) == 11


@pytest.mark.parametrize(
    "manifiestos",
    [
        [],
        ["REPETIDO", " repetido "],
        [f"MANIFIESTO-{index}" for index in range(101)],
    ],
)
def test_lote_rechaza_vacio_duplicados_y_mas_de_cien(
    manifiestos: list[str],
) -> None:
    with pytest.raises(ValueError):
        ConsultaLoteInput(manifiestos=manifiestos, fecha_fin=date(2026, 7, 14))
