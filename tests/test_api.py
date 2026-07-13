"""Pruebas de humo y contrato HTTP de FastAPI."""

from datetime import date
from typing import Literal

import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.api.routes import get_orchestrator, get_portal_health_checker
from app.config import Settings
from app.main import create_app
from app.models import ConsultaInput, EstadoConsulta, Modalidad, ResultadoTICA


class FakeOrchestrator:
    def __init__(self, estado: EstadoConsulta = EstadoConsulta.NOT_IMPLEMENTED) -> None:
        self.estado = estado
        self.entrada: ConsultaInput | None = None

    async def consultar(self, entrada: ConsultaInput) -> ResultadoTICA:
        self.entrada = entrada
        return ResultadoTICA(
            estado=self.estado,
            modalidad=Modalidad.AEREO,
            identificador=entrada.manifiesto,
            motivo="respuesta_de_prueba",
        )


class FakePortalChecker:
    def __init__(self, available: bool) -> None:
        self.available = available

    async def disponible(self) -> bool:
        return self.available


async def solicitar(
    method: str,
    path: str,
    *,
    orchestrator: FakeOrchestrator | None = None,
    portal_available: bool = True,
    json_body: object | None = None,
) -> Response:
    application = create_app(Settings(app_env="test"))
    application.dependency_overrides[get_orchestrator] = lambda: (
        orchestrator or FakeOrchestrator()
    )
    application.dependency_overrides[get_portal_health_checker] = lambda: (
        FakePortalChecker(portal_available)
    )
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://test",
    ) as client:
        return await client.request(method, path, json=json_body)


@pytest.mark.asyncio
async def test_health_responde_200() -> None:
    response = await solicitar("GET", "/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "component": "service"}


@pytest.mark.asyncio
async def test_health_portal_responde_200_cuando_tica_esta_disponible() -> None:
    response = await solicitar("GET", "/v1/health/portal", portal_available=True)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "component": "portal"}


@pytest.mark.asyncio
async def test_health_portal_responde_503_cuando_tica_no_esta_disponible() -> None:
    response = await solicitar("GET", "/v1/health/portal", portal_available=False)

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "component": "portal"}


@pytest.mark.asyncio
async def test_consulta_invalida_responde_422_sin_llamar_orquestador() -> None:
    orchestrator = FakeOrchestrator()

    response = await solicitar(
        "POST",
        "/v1/consultas",
        orchestrator=orchestrator,
        json_body={"manifiesto": ""},
    )

    assert response.status_code == 422
    assert orchestrator.entrada is None


@pytest.mark.asyncio
async def test_consulta_valida_delega_manifiesto_y_fecha_fin() -> None:
    orchestrator = FakeOrchestrator()

    response = await solicitar(
        "POST",
        "/v1/consultas",
        orchestrator=orchestrator,
        json_body={"manifiesto": "ENGB2600229", "fecha_fin": "2026-07-13"},
    )

    assert response.status_code == 200
    assert orchestrator.entrada is not None
    assert orchestrator.entrada.manifiesto == "ENGB2600229"
    assert orchestrator.entrada.fecha_fin == date(2026, 7, 13)
    assert response.json()["estado"] == "not_implemented"


@pytest.mark.parametrize("estado", list(EstadoConsulta))
@pytest.mark.asyncio
async def test_api_serializa_todos_los_estados(estado: EstadoConsulta) -> None:
    response = await solicitar(
        "POST",
        "/v1/consultas",
        orchestrator=FakeOrchestrator(estado),
        json_body={"manifiesto": "ENGB2600229", "fecha_fin": "2026-07-13"},
    )

    body: dict[str, Literal[
        "ok",
        "pending",
        "stale",
        "unavailable",
        "needs_review",
        "not_found",
        "not_implemented",
    ] | object] = response.json()
    assert response.status_code == 200
    assert body["estado"] == estado.value


def test_openapi_exige_solo_manifiesto_y_fecha_fin_como_entrada() -> None:
    schema = create_app(Settings(app_env="test")).openapi()
    input_schema = schema["components"]["schemas"]["ConsultaInput"]

    assert set(input_schema["required"]) == {"manifiesto", "fecha_fin"}
    assert set(input_schema["properties"]) == {"manifiesto", "fecha_fin"}
    assert input_schema["additionalProperties"] is False


def test_openapi_contiene_los_diez_campos_y_excluye_los_retirados() -> None:
    schemas = create_app(Settings(app_env="test")).openapi()["components"]["schemas"]
    fields = {
        *schemas["DatosMomento1"]["properties"],
        *schemas["DatosMomento2"]["properties"],
        *schemas["DatosMomento3"]["properties"],
    }

    assert fields == {
        "fecha_arribo",
        "transportista",
        "movimiento_inventario",
        "almacen_fiscal",
        "fecha_ingreso_regimen",
        "fecha_movimiento_inventario",
        "bultos",
        "peso_bruto",
        "dua_nacionalizacion",
        "fecha_dua",
    }
    assert "partidas_arancelarias" not in fields
    assert "valor_aduanas_impuestos" not in fields
    assert schemas["DatosMomento2"]["properties"]["bultos"]["anyOf"][0]["type"] == "integer"
    assert (
        schemas["DatosMomento2"]["properties"]["peso_bruto"]["anyOf"][0]["type"]
        == "integer"
    )


def test_openapi_publica_los_siete_estados() -> None:
    schemas = create_app(Settings(app_env="test")).openapi()["components"]["schemas"]

    assert set(schemas["EstadoConsulta"]["enum"]) == {
        estado.value for estado in EstadoConsulta
    }


def test_openapi_documenta_indisponibilidad_del_portal() -> None:
    paths = create_app(Settings(app_env="test")).openapi()["paths"]

    assert "503" in paths["/v1/health/portal"]["get"]["responses"]
