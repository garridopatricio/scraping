# Scrapping TICA

## Resumen del proyecto

Scrapping TICA es un microservicio Python que automatiza la consulta de datos publicos de importacion en el portal TICA de Costa Rica. A partir de un manifiesto y una fecha, identifica automaticamente si la carga es aerea o maritima, recorre el flujo correspondiente y normaliza la informacion de arribo, movimiento de inventario y DUA para su futura integracion con RAGA Orders.

El proyecto usa FastAPI, Pydantic y Playwright. La prueba de concepto ya valido los recorridos aereo y maritimo; la infraestructura productiva y el contrato de la API estan terminados, mientras que la migracion del scraping real se desarrolla por modalidad. La modalidad terrestre es condicional y no forma parte del alcance activo.

## Resumen de sprints

| Sprint | Alcance | Estado actual |
|---|---|---|
| Sprint 0 - PoC y planificacion | Validar casos reales, reglas de negocio y viabilidad del portal TICA. | **Completado**. Gate M0 cerrado. |
| Sprint 1 - Infra base | Crear arquitectura, modelos, navegador, estrategias, cache, logging, API y contrato. | **Completado**. 9 de 9 tareas; hito M1 aprobado. |
| Sprint 2 - Modalidad aerea | Migrar el flujo aereo, preparar fixtures, implementar los tres momentos y validar con QA. | **En curso**. 0 de 7 tareas completadas; TICA-020 (fixtures aereos) en curso. |
| Sprint 3 - Modalidad maritima | Migrar el flujo maritimo, sus filtros y la regla de DUA de nacionalizacion. | **Pendiente**. Inicia despues del Sprint 2. |
| Sprint 4 - Integracion RAGA Orders | Integrar el cliente HTTP, los campos TICA y su visualizacion en RAGA Orders. | **Pendiente**. |
| Sprint 5 - QA integral y cierre | Validar estados, degradacion, CAPTCHA y reglas con casos reales. | **Pendiente**. |
| Sprint 6 - Terrestre | Incorporar la modalidad terrestre si se confirma su necesidad y se reciben insumos. | **Condicional / fuera del alcance actual**. |

## Estado actual

- Fase vigente: Sprint 2 - Modalidad aerea.
- Tarea activa: TICA-020 - fixtures aereos sanitizados.
- Entrada vigente: `manifiesto` y `fecha_fin`.
- Modalidad: detectada automaticamente como aerea o maritima desde Master.
- Arquitectura: el codigo de `app/` es autonomo y no importa el archivo de la PoC.

El seguimiento vigente se mantiene en [Sprint 2 - avances](docs/SPRINT-2-AVANCES.md).

## Documentacion

- [Backlog de desarrollo](docs/BACKLOG-DESARROLLO.md)
- [Proceso de consulta TICA paso a paso](docs/PROCESO-CONSULTA-TICA-PASO-A-PASO.md)
- [Tareas del proyecto Dokka Scrapping](docs/TAREAS-DOKKA-SCRAPPING.md)
- [Indice completo de documentacion](docs/README.md)
- [Cierre del Sprint 0](docs/SPRINT-0-CIERRE.md)
- [Avances del Sprint 1](docs/SPRINT-1-AVANCES.md)
- [Avances del Sprint 2](docs/SPRINT-2-AVANCES.md)

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

- `POST /v1/consultas`: recibe `manifiesto` y `fecha_fin`.
- `GET /v1/health`: salud del microservicio.
- `GET /v1/health/portal`: conectividad con la portada de TICA; no consulta manifiestos.

Ejemplo de entrada:

```json
{
  "manifiesto": "ENGB2600229",
  "fecha_fin": "2026-07-13"
}
```

Ejemplo abreviado de respuesta mientras el flujo de modalidad siga pendiente de migracion:

```json
{
  "estado": "not_implemented",
  "modalidad": "maritimo",
  "identificador": "ENGB2600229",
  "motivo": "flujo_modalidad_pendiente_de_migracion",
  "desde_cache": false
}
```

Los flujos completos aun responden `not_implemented` hasta migrar aereo en Sprint 2 y maritimo en Sprint 3.

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
