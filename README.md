# Scrapping TICA API

Microservicio FastAPI para consultar información pública de importación en TICA mediante Playwright. Es independiente del sistema consumidor y publica resultados normalizados para cargas aéreas, marítimas y terrestres.

## Capacidades

- Aéreo y marítimo: consulta uno o varios conocimientos, detecta modalidad y extrae arribo, transportista, movimientos, depósitos, detenciones y DUA.
- Terrestre: recibe Número DUA, entrega CAPTCHA para resolución humana y continúa hacia detalle, Manifiesto/Stock, movimientos y detenciones.
- Contrato común: `momento1`, `momento2`, `momento3`, estados controlados, normalización y logs JSON correlacionados.
- Limpieza garantizada de página, BrowserContext y navegador.

La API no persiste Shipping Documents ni conoce la interfaz del cliente. Cada consumidor decide cómo presentar el CAPTCHA y dónde guardar el resultado. RAGA Orders/Dokka es el consumidor de referencia actual.

## Requisitos

- Python 3.12.
- Chromium de Playwright.

## Instalación

```powershell
python -m venv .venv
& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
& ".venv\Scripts\python.exe" -m playwright install chromium
Copy-Item ".env.example" ".env"
```

No copie `.venv` entre equipos ni publique `.env`.

## Ejecutar localmente

```powershell
& ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

En Windows no use `--reload`: el event loop seleccionado puede impedir que Playwright cree subprocesos.

## Endpoints

| Método | Ruta | Uso |
|---|---|---|
| POST | `/v1/consultas` | Consultas aéreas/marítimas en lote |
| POST | `/v1/consultas-terrestres` | Crear sesión terrestre y obtener CAPTCHA |
| POST | `/v1/consultas-terrestres/{session_id}/resolver` | Resolver CAPTCHA e iniciar extracción |
| GET | `/v1/consultas-terrestres/{session_id}` | Consultar estado/resultado |
| POST | `/v1/consultas-terrestres/{session_id}/regenerar` | Solicitar otra imagen explícitamente |
| DELETE | `/v1/consultas-terrestres/{session_id}` | Liberar la sesión temporal |
| GET | `/v1/health` | Salud del proceso |
| GET | `/v1/health/portal` | Conectividad con TICA |

El `DELETE` terrestre no elimina datos del consumidor; solo libera recursos temporales.

## Verificación

```powershell
& ".venv\Scripts\python.exe" -m pytest
& ".venv\Scripts\python.exe" -m ruff check app tests
& ".venv\Scripts\python.exe" -m mypy app tests
```

## Documentación

- [Índice técnico](docs/README.md)
- [Contrato API](docs/SPRINT-1-CONTRATO-API.md)
- [Integración para aplicaciones cliente](docs/INTEGRACION-API-TICA.md)
- [Guía FastAPI](docs/GUIA-FASTAPI.md)
- [Proceso por modalidad](docs/PROCESO-CONSULTA-TICA-PASO-A-PASO.md)
- [Despliegue en producción](docs/PASO-A-PRODUCCION-TICA.md)

## Operación

Las sesiones CAPTCHA permanecen en memoria. La configuración vigente debe usar un solo worker; escalar horizontalmente requiere afinidad o estado compartido. `structlog` escribe JSON a stdout y Uvicorn agrega el access log HTTP.
