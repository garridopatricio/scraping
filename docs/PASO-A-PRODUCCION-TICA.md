# Despliegue en producción de Scrapping TICA API

## Objetivo

Ejecutar FastAPI y Playwright como servicio independiente, accesible por aplicaciones backend. La referencia utiliza Python/Uvicorn administrado como daemon desde Ploi; no requiere Docker.

## Instalación Linux

```bash
cd /ruta/Scrapping
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install .
./.venv/bin/python -m playwright install --with-deps chromium
```

Crear `.env` sin versionarlo:

```dotenv
TICA_APP_ENV=production
TICA_LOG_LEVEL=INFO
TICA_BROWSER_HEADLESS=true
TICA_BROWSER_TIMEOUT_MS=30000
TICA_TERRESTRIAL_SESSION_TTL_SECONDS=180
TICA_TERRESTRIAL_PROCESSING_TIMEOUT_SECONDS=180
TICA_TERRESTRIAL_MAX_SESSIONS=3
```

## Validación manual

```bash
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
curl --fail http://127.0.0.1:8000/v1/health
curl --fail http://127.0.0.1:8000/v1/health/portal
```

No use `--reload` en producción.

## Daemon Ploi

Configurar:

- directorio: `/ruta/Scrapping`;
- comando: `/ruta/Scrapping/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1`;
- reinicio automático;
- captura y rotación de stdout/stderr.

El puerto puede cambiar, pero el reverse proxy o consumidor debe usar el mismo. Escuchar en `127.0.0.1` evita exposición directa cuando consumidor y scraper comparten servidor.

Se exige un worker porque los BrowserContext y sesiones CAPTCHA viven en memoria. El escalamiento horizontal requiere afinidad o rediseño de estado.

## Seguridad

La API actual no autentica consumidores. Manténgala en red privada o detrás de un gateway con autenticación, TLS, límites y allowlist. No permita acceso directo desde navegadores públicos.

## Logs

`structlog` escribe JSON con evento, correlación, tipo/número de búsqueda, modalidad, estado y duración. Uvicorn genera access logs HTTP. Ploi debe capturar ambos, rotarlos y alertar ante errores repetidos, timeouts o crecimiento de sesiones.

## Actualización

```bash
git pull --ff-only
./.venv/bin/python -m pip install .
./.venv/bin/python -m playwright install chromium
```

Ejecutar pruebas/health checks y reiniciar el daemon. Para rollback, regresar mediante el procedimiento Git aprobado, reinstalar dependencias y reiniciar; no sobrescribir `.env`.

## Checklist

- [ ] Dependencias y Chromium instalados.
- [ ] `.env` productivo protegido.
- [ ] Un solo worker activo.
- [ ] Health checks correctos.
- [ ] Prueba aérea/marítima completada.
- [ ] Prueba terrestre con CAPTCHA incorrecto y correcto completada.
- [ ] Logs y rotación revisados.
- [ ] Acceso restringido a backends autorizados.
