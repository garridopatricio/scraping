"""Sanitizacion de HTML real para fixtures offline de TICA."""

from __future__ import annotations

import re
from html import escape
from pathlib import Path

from playwright.async_api import Page


def sanitizar_html(html: str, secretos: set[str]) -> str:
    """Elimina identificadores reales sin alterar tablas, enlaces ni etiquetas."""

    resultado = html
    for indice, secreto in enumerate(sorted(secretos, key=len, reverse=True), start=1):
        if secreto:
            reemplazo = (
                ("9" * len(secreto))
                if secreto.isdigit()
                else f"IDENTIFICADOR-SANITIZADO-{indice}"
            )
            resultado = re.sub(
                re.escape(secreto),
                reemplazo,
                resultado,
                flags=re.IGNORECASE,
            )

    # El estado GeneXus y las grillas ocultas duplican todos los datos visibles.
    resultado = re.sub(
        r'(<input\b[^>]*\btype=["\']hidden["\'][^>]*\bvalue=)(?P<quote>["\']).*?(?P=quote)',
        r'\1"ESTADO-SANITIZADO"',
        resultado,
        flags=re.IGNORECASE,
    )
    # Columnas sensibles conocidas de las grillas TICA.
    campos_sensibles = {
        "CGNROMIC": "99999999",  # manifiesto
        "CGNROCON": "9999999999",  # conocimiento
        "CGGARACON": "999999999999",  # RUC garante
        "CGCONCONSIG": "999999999999",  # identificacion consignatario
        "CGRSOCCONSIG": "CONSIGNATARIO SANITIZADO",
        "VCGMOVCONSIG": "999999999999",  # identificacion consignatario en Stock
        "VCONSNOM": "CONSIGNATARIO SANITIZADO",  # nombre consignatario en Stock
        "VGARANOM": "RAZON SOCIAL SANITIZADA",
        "NUME_CORRE": "999999",  # numero DUA
        "CGMOVSKID": "99999999",  # numero de movimiento de inventario
        "VUBICACION": "DEPOSITO SANITIZADO",
        "VRGRSOC": "RAZON SOCIAL SANITIZADA",
    }
    for campo, reemplazo in campos_sensibles.items():
        def reemplazar_campo(match: re.Match[str], value: str = reemplazo) -> str:
            return f"{match.group(1)}{value}{match.group(3)}"

        resultado = re.sub(
            rf'(<(?:span|a)\b[^>]*\bid=["\'][^"\']*{campo}[^"\']*["\'][^>]*>)(.*?)(</(?:span|a)>)',
            reemplazar_campo,
            resultado,
            flags=re.IGNORECASE | re.DOTALL,
        )

    # Nombres y razones sociales aparecen con identificadores distintos según la
    # pantalla GeneXus. Se reemplazan por familia para no depender de cada versión.
    resultado = re.sub(
        r'(<(?:span|a)\b[^>]*\bid=["\'][^"\']*(?:NOM|RSOC|CONSIG)[^"\']*["\'][^>]*>)(.*?)(</(?:span|a)>)',
        lambda match: f"{match.group(1)}DATO PERSONAL SANITIZADO{match.group(3)}",
        resultado,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # DUA visible como valor compuesto.
    resultado = re.sub(
        r"(?<!\d)(\d{3})[-\s]+(20\d{2})[-\s]+(\d{5,})(?!\d)",
        r"\1-ANIO-SANITIZADO-DUA-SANITIZADO",
        resultado,
    )
    # RUC, cedulas, manifiestos y conocimientos largos restantes.
    resultado = re.sub(
        r"(?<![\d.])\d{9,}(?![\d.])",
        lambda match: "9" * len(match.group(0)),
        resultado,
    )
    # Tokens cifrados de navegacion; se conserva el endpoint y la existencia del query.
    resultado = re.sub(
        r'((?:href|action)=["\'][^"\'?#\s]+)\?[^"\']+(["\'])',
        r'\1?PARAMETRO-SANITIZADO\2',
        resultado,
        flags=re.IGNORECASE,
    )
    # Parametros convencionales, por si TICA incorpora URLs legibles.
    resultado = re.sub(
        r"([?&](?:id|codigo|nro|numero|key|token|gxid)=[^&\"'<>\s]+)",
        lambda match: match.group(0).split("=", 1)[0] + "=PARAMETRO-SANITIZADO",
        resultado,
        flags=re.IGNORECASE,
    )
    resultado = re.sub(
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        "EMAIL-SANITIZADO",
        resultado,
    )
    return resultado


class CapturadorFixtureHTML:
    """Guarda exclusivamente la representacion sanitizada de cada pantalla."""

    def __init__(self, destino: Path, secretos: set[str]) -> None:
        self.destino = destino
        self.secretos = secretos
        self.archivos: list[Path] = []

    async def __call__(self, nombre: str, page: Page) -> None:
        html = sanitizar_html(await page.content(), self.secretos)
        html = (
            "<!-- Fixture derivado de HTML real TICA; datos sanitizados. -->\n"
            f"<!-- Pantalla: {escape(nombre)} -->\n{html}"
        )
        self.destino.mkdir(parents=True, exist_ok=True)
        archivo = self.destino / f"{nombre}.html"
        archivo.write_text(html, encoding="utf-8")
        self.archivos.append(archivo)
