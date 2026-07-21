"""Contrato de entrada y salida para consultas de embarques en TICA."""

from datetime import UTC, date, datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.models.enums import EstadoConsulta, Modalidad

MAX_MANIFIESTOS_POR_LOTE = 100


def quitar_comillas_envolventes(value: object) -> object:
    """Evita enviar a TICA comillas copiadas como parte del conocimiento."""

    if not isinstance(value, str):
        return value
    return value.strip().strip("\"'").strip()


class ModeloTICA(BaseModel):
    """Configuracion comun para modelos estrictos del servicio."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ConsultaInput(ModeloTICA):
    """Entrada unitaria interna usada por el orquestador existente.

    La API publica recibe ``ConsultaLoteInput`` y crea una instancia por manifiesto.
    """

    manifiesto: str = Field(min_length=1, max_length=200)
    fecha_inicio: date | None = None
    fecha_fin: date

    @field_validator("manifiesto", mode="before")
    @classmethod
    def normalizar_manifiesto(cls, value: object) -> object:
        return quitar_comillas_envolventes(value)

    @model_validator(mode="after")
    def validar_fechas(self) -> Self:
        validar_ventana_fechas(self.fecha_inicio, self.fecha_fin)
        return self


ManifiestoConsulta = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]


class ConsultaLoteInput(ModeloTICA):
    """Solicitud publica uniforme para consultar uno o varios manifiestos."""

    manifiestos: list[ManifiestoConsulta] = Field(
        min_length=1,
        max_length=MAX_MANIFIESTOS_POR_LOTE,
    )
    fecha_inicio: date | None = None
    fecha_fin: date

    @field_validator("manifiestos", mode="before")
    @classmethod
    def normalizar_manifiestos(cls, values: object) -> object:
        if not isinstance(values, list):
            return values
        return [quitar_comillas_envolventes(value) for value in values]

    @field_validator("manifiestos")
    @classmethod
    def rechazar_duplicados(cls, values: list[str]) -> list[str]:
        """Evita consultar dos veces el mismo manifiesto dentro del lote."""

        normalized = [value.casefold() for value in values]
        if len(normalized) != len(set(normalized)):
            raise ValueError("manifiestos no puede contener valores repetidos")
        return values

    @model_validator(mode="after")
    def validar_fechas(self) -> Self:
        validar_ventana_fechas(self.fecha_inicio, self.fecha_fin)
        return self


def validar_ventana_fechas(fecha_inicio: date | None, fecha_fin: date) -> None:
    """Valida la ventana solo cuando el consumidor envia una fecha inicial."""

    if fecha_inicio is None:
        return
    if fecha_inicio > fecha_fin:
        raise ValueError("fecha_inicio no puede ser posterior a fecha_fin")
    if (fecha_fin - fecha_inicio).days > 14:
        raise ValueError("la ventana entre fecha_inicio y fecha_fin no puede superar 15 dias")


class DatosMomento1(ModeloTICA):
    """Datos de arribo obtenidos desde Conocimientos de Embarque."""

    fecha_arribo: date | None = None
    transportista: str | None = Field(default=None, min_length=1, max_length=300)


class DatosMovimiento(ModeloTICA):
    """Movimiento individual confirmado desde Depositos y Detenciones."""

    movimiento_inventario: str | None = Field(default=None, min_length=1, max_length=100)
    almacen_fiscal: str | None = Field(default=None, min_length=1, max_length=300)
    fecha_ingreso_regimen: date | None = None
    fecha_movimiento_inventario: datetime | None = None
    bultos: int | None = Field(default=None, ge=0)
    peso_bruto: float | None = Field(default=None, ge=0)


class DatosMomento2(DatosMovimiento):
    """Datos operativos; maritimo puede publicar varios movimientos."""

    movimientos: list[DatosMovimiento] = Field(default_factory=list)


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


class ResultadoManifiesto(ModeloTICA):
    """Datos publicados bajo la clave del manifiesto consultado."""

    estado: EstadoConsulta
    modalidad: Modalidad | None = None
    momento1: DatosMomento1 = Field(default_factory=DatosMomento1)
    momento2: DatosMomento2 = Field(default_factory=DatosMomento2)
    momento3: DatosMomento3 = Field(default_factory=DatosMomento3)
    motivo: str | None = Field(default=None, min_length=1, max_length=300)
    desde_cache: bool = False
    consultado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def desde_resultado(
        cls,
        resultado: ResultadoTICA,
    ) -> "ResultadoManifiesto":
        """Oculta el identificador interno porque el manifiesto es la clave JSON."""

        return cls(
            estado=resultado.estado,
            modalidad=resultado.modalidad,
            momento1=resultado.momento1,
            momento2=resultado.momento2,
            momento3=resultado.momento3,
            motivo=resultado.motivo,
            desde_cache=resultado.desde_cache,
            consultado_en=resultado.consultado_en,
        )


type ConsultaLoteResultado = dict[str, ResultadoManifiesto]
