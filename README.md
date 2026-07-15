# Scrapping TICA

## Resumen del proyecto

Scrapping TICA es un microservicio Python que automatiza la consulta de datos publicos de importacion en el portal TICA de Costa Rica. A partir de uno o varios manifiestos, una `fecha_fin` y una `fecha_inicio` opcional, procesa cada manifiesto, identifica automaticamente si la carga es aerea o maritima y normaliza la informacion de arribo, movimiento de inventario y DUA para su futura integracion con RAGA Orders.

El proyecto usa FastAPI, Pydantic y Playwright. La prueba de concepto ya valido los recorridos aereo y maritimo; la infraestructura productiva y el contrato de la API estan terminados, mientras que la migracion del scraping real se desarrolla por modalidad. La modalidad terrestre es condicional y no forma parte del alcance activo.

## Resumen de sprints

| Sprint | Alcance | Estado actual |
|---|---|---|
| Sprint 0 - PoC y planificacion | Validar casos reales, reglas de negocio y viabilidad del portal TICA. | **Completado**. Gate M0 cerrado. |
| Sprint 1 - Infra base | Crear arquitectura, modelos, navegador, estrategias, cache, logging, API y contrato. | **Completado**. 9 de 9 tareas; hito M1 aprobado. |
| Sprint 2 - Modalidad aerea | Migrar el flujo aereo, preparar fixtures, implementar los tres momentos y validar con QA. | **Completado**. 7 de 7 tareas; M2 aprobado con limitacion documentada por falta de casos reales sin arribo y multi-ING. |
| Sprint 3 - Modalidad maritima | Migrar el flujo maritimo, sus filtros y la regla de DUA de nacionalizacion. | **Completado**. 7 de 7 tareas; M3 aprobado. |
| Sprint 4 - Integracion RAGA Orders | Integrar el cliente HTTP, los campos TICA y su visualizacion en RAGA Orders. | **Pendiente**. |
| Sprint 5 - QA integral y cierre | Validar estados, degradacion, CAPTCHA y reglas con casos reales. | **Pendiente**. |
| Sprint 6 - Terrestre | Incorporar la modalidad terrestre si se confirma su necesidad y se reciben insumos. | **Condicional / fuera del alcance actual**. |

## Estado actual

- Fase cerrada: Sprint 2 - Modalidad aerea; hito M2 aprobado.
- TICA-020: completada con excepcion aceptada. No se dispuso de casos reales sin arribo ni multi-ING; ambas ramas quedan cubiertas mediante fixtures estructurales y deben revalidarse cuando aparezcan datos reales.
- TICA-026: completada; QA confirmado con los casos aereos disponibles.
- Fase cerrada: Sprint 3 - Modalidad maritima; M3 aprobado.
- Siguiente fase: Sprint 4 - Integracion RAGA Orders.
- La cedula maritima `095144` es configuracion interna; anticipados y varias lineas ya estan implementados.
- Entrada vigente: `manifiestos` (lista de 1 a 100), `fecha_fin` obligatoria y `fecha_inicio` opcional.
- Ejecucion del lote: asincrona en I/O, pero secuencial por manifiesto y en orden de entrada.
- Modalidad: detectada automaticamente como aerea o maritima desde Master.
- Arquitectura: el codigo de `app/` es autonomo y no importa el archivo de la PoC.

El seguimiento vigente se mantiene en [Sprint 3 - avances](docs/SPRINT-3-AVANCES.md).

## Documentacion

- [Backlog de desarrollo](docs/BACKLOG-DESARROLLO.md)
- [Proceso de consulta TICA paso a paso](docs/PROCESO-CONSULTA-TICA-PASO-A-PASO.md)
- [Tareas del proyecto Dokka Scrapping](docs/TAREAS-DOKKA-SCRAPPING.md)
- [Indice completo de documentacion](docs/README.md)
- [Cierre del Sprint 0](docs/SPRINT-0-CIERRE.md)
- [Avances del Sprint 1](docs/SPRINT-1-AVANCES.md)
- [Avances del Sprint 2](docs/SPRINT-2-AVANCES.md)
- [Avances del Sprint 3](docs/SPRINT-3-AVANCES.md)

## Requisitos

- Python 3.12.
- Chromium de Playwright.

## Instalacion local en Windows

Desde la raiz del repositorio:

```powershell
python -m venv .venv
& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
& ".venv\Scripts\python.exe" -m playwright install chromium
```

Copiar la configuracion de ejemplo solamente cuando sea necesario personalizar valores:

```powershell
Copy-Item ".env.example" ".env"
```

No guardar secretos en `.env.example` ni subir `.env` al repositorio.

## Verificacion

```powershell
& ".venv\Scripts\python.exe" -m pytest
& ".venv\Scripts\python.exe" -m ruff check app tests
& ".venv\Scripts\python.exe" -m mypy app tests
```

## Ejecutar la API

```powershell
& ".venv\Scripts\python.exe" -m uvicorn app.main:app
```

En Windows no se debe usar `--reload` con la configuracion actual: Uvicorn selecciona un event loop incompatible con los subprocesos que necesita Playwright.

Rutas disponibles:

- `POST /v1/consultas`: recibe uno o varios `manifiestos`, una `fecha_fin` compartida y, opcionalmente, `fecha_inicio`.
- `GET /v1/health`: salud del microservicio.
- `GET /v1/health/portal`: conectividad con la portada de TICA; no consulta manifiestos.

Ejemplo de entrada:

```json
{
  "manifiestos": ["ENGB2600229", "MANIFIESTO-B"],
  "fecha_fin": "2026-07-14"
}
```

Si se omite `fecha_inicio`, el servicio deja vacío ese campo en TICA, igual que la consulta manual. Si se incluye, debe ser menor o igual a `fecha_fin` y la ventana no puede superar 15 días inclusivos.

Ejemplo abreviado de respuesta:

```json
{
  "ENGB2600229": {
    "estado": "ok",
    "modalidad": "maritimo",
    "momento1": {},
    "momento2": {"movimientos": []},
    "momento3": {},
    "motivo": null,
    "desde_cache": false
  },
  "MANIFIESTO-B": {
    "estado": "not_found",
    "modalidad": null,
    "momento1": {},
    "momento2": {},
    "momento3": {},
    "motivo": "manifiesto_no_encontrado",
    "desde_cache": false
  }
}
```

Cada clave de primer nivel es el manifiesto recibido y su valor contiene los datos de esa consulta. No existen los envoltorios `regla` ni `resultados`. La misma estructura se usa para un solo manifiesto. Los manifiestos se procesan uno por uno para no ejecutar sesiones paralelas contra el portal publico; un fallo individual no detiene el resto del lote.

Los flujos aereo y maritimo estan migrados y validados. Sprint 4 integra estas respuestas
con RAGA Orders.

## Estructura

```text
scrapping-tica/
|-- app/
|   |-- cache/
|   |-- models/
|   |-- orchestrator/
|   `-- scraper/
|-- docs/
|-- tests/
|-- .env.example
|-- .gitignore
`-- pyproject.toml
```

`.venv/`, `.env`, la copia local de referencia de la PoC y sus salidas estan excluidas mediante `.gitignore`.
