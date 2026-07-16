"""Pruebas de humo y contrato HTTP de FastAPI."""

from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.api.routes import get_lote_orchestrator, get_portal_health_checker
from app.config import Settings
from app.main import create_app
from app.models import (
    ConsultaLoteInput,
    ConsultaLoteResultado,
    EstadoConsulta,
    Modalidad,
    ResultadoManifiesto,
)


class FakeLoteOrchestrator:
    def __init__(self, estado: EstadoConsulta = EstadoConsulta.NOT_IMPLEMENTED) -> None:
        self.estado = estado
        self.entrada: ConsultaLoteInput | None = None

    async def consultar(self, entrada: ConsultaLoteInput) -> ConsultaLoteResultado:
        self.entrada = entrada
        return {
            manifest: ResultadoManifiesto(
                estado=self.estado,
                modalidad=Modalidad.AEREO,
                motivo="respuesta_de_prueba",
            )
            for manifest in entrada.manifiestos
        }


class FakePortalChecker:
    def __init__(self, available: bool) -> None:
        self.available = available

    async def disponible(self) -> bool:
        return self.available


async def solicitar(
    method: str,
    path: str,
    *,
    orchestrator: FakeLoteOrchestrator | None = None,
    portal_available: bool = True,
    json_body: object | None = None,
) -> Response:
    application = create_app(Settings(app_env="test"))
    application.dependency_overrides[get_lote_orchestrator] = lambda: (
        orchestrator or FakeLoteOrchestrator()
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
    orchestrator = FakeLoteOrchestrator()

    response = await solicitar(
        "POST",
        "/v1/consultas",
        orchestrator=orchestrator,
        json_body={"manifiestos": []},
    )

    assert response.status_code == 422
    assert orchestrator.entrada is None


@pytest.mark.asyncio
async def test_un_manifiesto_usa_el_mismo_contrato_de_lote() -> None:
    orchestrator = FakeLoteOrchestrator()

    response = await solicitar(
        "POST",
        "/v1/consultas",
        orchestrator=orchestrator,
        json_body={"manifiestos": ["ENGB2600229"], "fecha_fin": "2026-07-13"},
    )

    assert response.status_code == 200
    assert orchestrator.entrada is not None
    assert orchestrator.entrada.manifiestos == ["ENGB2600229"]
    assert orchestrator.entrada.fecha_inicio is None
    assert orchestrator.entrada.fecha_fin == date(2026, 7, 13)
    body = response.json()
    assert list(body) == ["ENGB2600229"]
    assert body["ENGB2600229"]["estado"] == "not_implemented"
    assert "manifiesto" not in body["ENGB2600229"]
    assert "identificador" not in body["ENGB2600229"]


@pytest.mark.asyncio
async def test_varios_manifiestos_conservan_orden_y_resultado_independiente() -> None:
    response = await solicitar(
        "POST",
        "/v1/consultas",
        json_body={
            "manifiestos": ["MANIFIESTO-A", "MANIFIESTO-B", "MANIFIESTO-C"],
            "fecha_fin": "2026-07-13",
        },
    )

    assert response.status_code == 200
    assert list(response.json()) == [
        "MANIFIESTO-A",
        "MANIFIESTO-B",
        "MANIFIESTO-C",
    ]


@pytest.mark.parametrize("estado", list(EstadoConsulta))
@pytest.mark.asyncio
async def test_api_serializa_todos_los_estados(estado: EstadoConsulta) -> None:
    response = await solicitar(
        "POST",
        "/v1/consultas",
        orchestrator=FakeLoteOrchestrator(estado),
        json_body={"manifiestos": ["MANIFIESTO-A"], "fecha_fin": "2026-07-13"},
    )

    assert response.status_code == 200
    assert response.json()["MANIFIESTO-A"]["estado"] == estado.value


def test_openapi_exige_manifiestos_y_fecha_fin_como_entrada() -> None:
    schema = create_app(Settings(app_env="test")).openapi()
    input_schema = schema["components"]["schemas"]["ConsultaLoteInput"]

    assert set(input_schema["required"]) == {"manifiestos", "fecha_fin"}
    assert set(input_schema["properties"]) == {
        "manifiestos",
        "fecha_inicio",
        "fecha_fin",
    }
    assert input_schema["properties"]["manifiestos"]["minItems"] == 1
    assert input_schema["properties"]["manifiestos"]["maxItems"] == 100
    assert input_schema["additionalProperties"] is False


def test_openapi_respuesta_publica_usa_manifiesto_como_clave() -> None:
    openapi = create_app(Settings(app_env="test")).openapi()
    schemas = openapi["components"]["schemas"]
    response_schema = openapi["paths"]["/v1/consultas"]["post"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    response_schema = schemas[response_schema["$ref"].rsplit("/", 1)[-1]]
    item_fields = set(schemas["ResultadoManifiesto"]["properties"])

    assert response_schema["type"] == "object"
    assert response_schema["additionalProperties"]["$ref"].endswith(
        "/ResultadoManifiesto"
    )
    assert "manifiesto" not in item_fields
    assert "identificador" not in item_fields
    assert {"momento1", "momento2", "momento3"} <= item_fields


def test_openapi_contiene_campos_confirmados_y_movimientos_maritimos() -> None:
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
        "estado_final",
        "movimientos",
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
