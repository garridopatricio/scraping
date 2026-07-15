"""Captura HTML real TICA, lo sanitiza en memoria y crea fixtures offline.

Uso:
    python tools/capturar_fixtures_aereo.py CONOCIMIENTO FECHA_FIN NOMBRE_CASO

Ejemplo:
    python tools/capturar_fixtures_aereo.py 1075388355 15/07/2026 ok_hawb
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models import ConsultaInput  # noqa: E402
from app.scraper.aereo import EstrategiaAerea  # noqa: E402
from app.scraper.fixture_html import CapturadorFixtureHTML  # noqa: E402
from app.scraper.portal import buscar_conocimiento  # noqa: E402


async def capturar(conocimiento: str, fecha_fin: str, caso: str) -> None:
    destino = Path("tests/fixtures/aereo") / caso
    capturador = CapturadorFixtureHTML(destino, {conocimiento})
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1000})
        page = await context.new_page()
        busqueda = await buscar_conocimiento(
            page,
            conocimiento,
            fecha_fin,
            f"fixture_{caso}",
            capturador=capturador,
        )
        resultado: dict[str, object]
        if not busqueda.fila:
            resultado = {"estado": "not_found", "valores": {}}
        elif busqueda.modalidad_detectada != "aereo":
            resultado = {"estado": "modalidad_no_aerea", "valores": {}}
        else:
            dia, mes, anio = (int(value) for value in fecha_fin.split("/"))
            entrada = ConsultaInput(
                manifiesto=conocimiento,
                fecha_fin=f"{anio:04d}-{mes:02d}-{dia:02d}",
            )
            resultado = await EstrategiaAerea(capturador).consultar(page, entrada, busqueda)
        await browser.close()

    print(json.dumps(resultado, ensure_ascii=False, default=str, indent=2))
    print(f"Fixtures sanitizados: {len(capturador.archivos)} en {destino.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("conocimiento")
    parser.add_argument("fecha_fin")
    parser.add_argument("caso")
    args = parser.parse_args()
    asyncio.run(capturar(args.conocimiento, args.fecha_fin, args.caso))


if __name__ == "__main__":
    main()
