"""Pruebas del contrato Pydantic de consultas TICA."""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.models import (
    ConsultaInput,
    ConsultaLoteInput,
    ContextoMaritimo,
    DatosMomento1,
    DatosMomento2,
    DatosMomento3,
    DatosMovimiento,
    EstadoConsulta,
    Modalidad,
    ResultadoTICA,
)
from app.scraper.domain import clasificar_modalidad_conocimiento


def test_estados_normalizados_son_los_siete_del_proyecto() -> None:
    assert {estado.value for estado in EstadoConsulta} == {
        "ok",
        "pending",
        "stale",
        "unavailable",
        "needs_review",
        "not_found",
        "not_implemented",
    }


def test_modalidades_actuales_incluyen_terrestre() -> None:
    assert {modalidad.value for modalidad in Modalidad} == {
        "aereo",
        "maritimo",
        "terrestre",
    }


def test_consulta_recibe_manifiesto_y_fecha_sin_pedir_modalidad() -> None:
    consulta = ConsultaInput(manifiesto="872219087246", fecha_fin=date(2026, 7, 13))

    assert consulta.manifiesto == "872219087246"
    assert consulta.fecha_inicio is None
    assert "modalidad" not in consulta.model_dump()


def test_consultas_eliminan_comillas_envolventes_de_los_manifiestos() -> None:
    fecha = date(2026, 7, 13)

    assert ConsultaInput(manifiesto=' "684115001954" ', fecha_fin=fecha).manifiesto == (
        "684115001954"
    )
    assert ConsultaLoteInput(
        manifiestos=["'684115001954'", '"HBL-2"'],
        fecha_fin=fecha,
    ).manifiestos == ["684115001954", "HBL-2"]


@pytest.mark.parametrize(
    ("fecha_inicio", "fecha_fin"),
    [("2026-07-14", "2026-07-13"), ("2026-06-28", "2026-07-13")],
)
def test_consulta_rechaza_ventana_invertida_o_mayor_a_quince_dias(
    fecha_inicio: str,
    fecha_fin: str,
) -> None:
    with pytest.raises(ValidationError):
        ConsultaInput.model_validate(
            {
                "manifiesto": "872219087246",
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            }
        )


@pytest.mark.parametrize("entrada", [{"fecha_fin": "2026-07-13"}, {"manifiesto": "872219087246"}])
def test_consulta_requiere_manifiesto_y_fecha(entrada: dict[str, str]) -> None:
    with pytest.raises(ValidationError, match="Field required"):
        ConsultaInput.model_validate(entrada)


@pytest.mark.parametrize("destino", ["Caldera", "Moín", "Puerto Limón"])
def test_clasificacion_existente_detecta_maritimo_por_descarga(destino: str) -> None:
    assert clasificar_modalidad_conocimiento({"desc_descarga": destino}) == "maritimo"


def test_clasificacion_existente_detecta_aereo_para_otras_descargas() -> None:
    assert clasificar_modalidad_conocimiento({"desc_descarga": "Juan Santamaria"}) == "aereo"


def test_clasificacion_existente_no_inventa_modalidad_sin_descarga() -> None:
    assert clasificar_modalidad_conocimiento({"desc_descarga": ""}) == "desconocida"


def test_modelos_rechazan_campos_fuera_del_contrato() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        DatosMomento1.model_validate(
            {"fecha_arribo": date(2026, 7, 13), "campo_inventado": "no"}
        )


def test_resultado_serializa_los_diez_campos_confirmados() -> None:
    resultado = ResultadoTICA(
        estado=EstadoConsulta.OK,
        modalidad=Modalidad.MARITIMO,
        identificador="ENGB2600229",
        momento1=DatosMomento1(
            fecha_arribo=date(2026, 6, 15),
            transportista="Transportista de prueba",
        ),
        momento2=DatosMomento2(
            movimiento_inventario="55808682",
            almacen_fiscal="A102",
            fecha_ingreso_regimen=date(2026, 6, 15),
            fecha_movimiento_inventario=datetime(2026, 6, 15, tzinfo=UTC),
            bultos=614,
            peso_bruto=7450,
        ),
        momento3=DatosMomento3(
            dua_nacionalizacion="005-2026-414387",
            fecha_dua=date(2026, 6, 16),
        ),
    )

    data = resultado.model_dump(mode="json")
    campos_salida = set(data["momento1"]) | set(data["momento2"]) | set(data["momento3"])

    assert campos_salida == {
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
        "movimientos",
    }
    assert "partidas_arancelarias" not in data
    assert "valor_aduanas_impuestos" not in data
    assert "dua_movilizacion" not in data
    assert data["momento2"]["bultos"] == 614
    assert data["momento2"]["peso_bruto"] == 7450
    assert data["momento2"]["movimientos"] == []


def test_momento2_admite_varios_movimientos_maritimos() -> None:
    momento = DatosMomento2(
        movimientos=[
            DatosMovimiento(movimiento_inventario="1458", bultos=40),
            DatosMovimiento(movimiento_inventario="1460", bultos=30),
        ]
    )

    assert [item.movimiento_inventario for item in momento.movimientos] == ["1458", "1460"]


def test_contexto_maritimo_mantiene_dua_movilizacion_como_dato_interno() -> None:
    contexto = ContextoMaritimo(
        dua_movilizacion="002-2026-050020",
        lugar_destino="A102",
    )

    assert contexto.dua_movilizacion == "002-2026-050020"


def test_cantidades_no_pueden_ser_negativas() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        DatosMomento2(bultos=-1)
