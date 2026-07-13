"""Contrato de entrada y salida para consultas de embarques en TICA."""

from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EstadoConsulta, Modalidad


class ModeloTICA(BaseModel):
    """Configuracion comun para modelos estrictos del servicio."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ConsultaInput(ModeloTICA):
    """Datos recibidos para iniciar una consulta.

    El usuario no elige la modalidad. El scraper busca el manifiesto/conocimiento
    y clasifica internamente el flujo como aereo o maritimo usando ``Desc Descarga``
    de la pantalla Master.
    """

    manifiesto: str = Field(min_length=1, max_length=200)
    fecha_fin: date


class DatosMomento1(ModeloTICA):
    """Datos de arribo obtenidos desde Conocimientos de Embarque."""

    fecha_arribo: date | None = None
    transportista: str | None = Field(default=None, min_length=1, max_length=300)


class DatosMomento2(ModeloTICA):
    """Datos operativos confirmados desde movimiento y Detenciones."""

    movimiento_inventario: str | None = Field(default=None, min_length=1, max_length=100)
    almacen_fiscal: str | None = Field(default=None, min_length=1, max_length=300)
    fecha_ingreso_regimen: date | None = None
    fecha_movimiento_inventario: datetime | None = None
    bultos: int | None = Field(default=None, ge=0)
    peso_bruto: int | None = Field(default=None, ge=0)


class DatosMomento3(ModeloTICA):
    """Datos de nacionalizacion confirmados desde el DUA final."""

    dua_nacionalizacion: str | None = Field(default=None, min_length=1, max_length=100)
    fecha_dua: date | None = None


class ContextoMaritimo(ModeloTICA):
    """Datos internos para navegar el flujo maritimo.

    Este modelo no forma parte de ``ResultadoTICA`` para impedir que el DUA de
    movilizacion se publique accidentalmente como DUA de nacionalizacion.
    """

    dua_movilizacion: str | None = Field(default=None, min_length=1, max_length=100)
    lugar_destino: str | None = Field(default=None, min_length=1, max_length=300)
    pedido_anticipado: bool = False


class ResultadoTICA(ModeloTICA):
    """Respuesta publica normalizada del microservicio."""

    estado: EstadoConsulta
    modalidad: Modalidad | None = None
    identificador: str = Field(min_length=1, max_length=200)
    momento1: DatosMomento1 = Field(default_factory=DatosMomento1)
    momento2: DatosMomento2 = Field(default_factory=DatosMomento2)
    momento3: DatosMomento3 = Field(default_factory=DatosMomento3)
    motivo: str | None = Field(default=None, min_length=1, max_length=300)
    desde_cache: bool = False
    consultado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))
