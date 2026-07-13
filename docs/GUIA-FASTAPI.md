# Guia de FastAPI - Scrapping TICA

Esta guia explica que hace FastAPI dentro del proyecto, como ejecutar la API localmente y como probar sus endpoints. Esta documentacion es independiente de Swagger y OpenAPI, que FastAPI genera automaticamente al iniciar el servicio.

## 1. Que es FastAPI

FastAPI es el framework web utilizado para exponer el scraper como un servicio HTTP.

Su responsabilidad en este proyecto es:

- Recibir solicitudes desde RAGA Orders u otro consumidor.
- Validar automaticamente los datos de entrada.
- Enviar la consulta al orquestador.
- Convertir el resultado Python en JSON.
- Publicar health checks.
- Generar documentacion OpenAPI interactiva.

FastAPI no contiene las reglas para navegar TICA. Tampoco decide como encontrar un DUA o seleccionar un movimiento. Esas responsabilidades pertenecen al orquestador y a los modulos de scraping.

## 2. Donde se encuentra

Los archivos principales son:

```text
app/
|-- main.py                 Crea la aplicacion FastAPI
|-- api/
|   `-- routes.py           Define los endpoints HTTP
|-- models/                 Define request, response y estados
|-- orchestrator/           Coordina cada consulta
`-- scraper/                Navega y extrae informacion de TICA
```

`app/main.py` es el punto de entrada del servidor. Su funcion es crear FastAPI, configurar el logging y registrar las rutas bajo `/v1`.

`app/api/routes.py` recibe las solicitudes y delega el trabajo. No debe contener selectores HTML ni reglas de negocio del portal.

## 3. Flujo de una solicitud

Cuando un consumidor llama a `POST /v1/consultas`, ocurre lo siguiente:

```text
Cliente o RAGA Orders
        |
        v
FastAPI valida el JSON
        |
        v
El endpoint llama al orquestador
        |
        v
El orquestador abre Playwright
        |
        v
Se busca el conocimiento en TICA
        |
        v
Master determina aereo o maritimo
        |
        v
La estrategia obtiene los datos
        |
        v
FastAPI serializa ResultadoTICA como JSON
```

La entrada no solicita modalidad. El servicio la determina usando `Desc Descarga` de Master.

## 4. Requisitos locales

- Python 3.12.
- Entorno virtual `.venv` creado dentro de `scrapping-tica`.
- Dependencias instaladas.
- Chromium de Playwright instalado.

Si el proyecto aun no esta preparado en el equipo:

```powershell
python -m venv .venv
& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
& ".venv\Scripts\python.exe" -m playwright install chromium
```

El operador `&` le indica a PowerShell que ejecute el archivo de Python ubicado dentro del entorno virtual.

## 5. Ejecutar FastAPI

Abrir PowerShell en la raiz de `scrapping-tica` y ejecutar:

```powershell
& ".venv\Scripts\python.exe" -m uvicorn app.main:app
```

Significado del comando:

- `.venv\Scripts\python.exe`: usa el Python aislado del proyecto.
- `-m uvicorn`: inicia el servidor ASGI.
- `app.main`: importa el archivo `app/main.py`.
- `:app`: utiliza la variable FastAPI llamada `app`.

### Importante en Windows

No agregar `--reload` con la configuracion actual. En Windows, Uvicorn 0.51 usa un event loop de tipo selector al activar la recarga, pero Playwright necesita crear un subproceso y requiere un event loop compatible con esa operacion.

El sintoma es que `/v1/health/portal` devuelve HTTP 500 y la terminal termina con:

```text
NotImplementedError
```

El servicio ahora convierte esta incompatibilidad en una indisponibilidad controlada, pero para que el navegador funcione se debe iniciar Uvicorn sin `--reload`. Cuando se modifica codigo, detener con `Ctrl+C` y volver a ejecutar el comando.

La salida debe indicar una direccion similar a:

```text
Uvicorn running on http://127.0.0.1:8000
```

Para detener el servidor, presionar `Ctrl+C`.

## 6. Documentacion generada automaticamente

Con el servidor ejecutandose:

| Recurso | URL | Uso |
|---|---|---|
| Swagger UI | `http://127.0.0.1:8000/docs` | Probar endpoints desde el navegador |
| ReDoc | `http://127.0.0.1:8000/redoc` | Leer el contrato en formato documental |
| OpenAPI | `http://127.0.0.1:8000/openapi.json` | Esquema procesable por otras herramientas |

Swagger permite seleccionar un endpoint, presionar **Try it out**, completar el JSON y ejecutar la solicitud.

Esta documentacion se genera desde:

- Las rutas de FastAPI.
- Los modelos Pydantic.
- Los tipos y validaciones.
- Los codigos HTTP declarados.

Por eso se actualiza al cambiar el codigo. Esta guia, en cambio, explica el funcionamiento general y debe mantenerse manualmente.

## 7. Endpoints disponibles

### `GET /v1/health`

Comprueba que FastAPI esta ejecutandose.

Respuesta esperada:

```json
{
  "status": "ok",
  "component": "service"
}
```

Este endpoint no abre TICA ni Playwright.

### `GET /v1/health/portal`

Comprueba si la portada de TICA responde.

- HTTP 200: el portal respondio.
- HTTP 503: TICA, Chromium o la navegacion inicial no estan disponibles.

No consulta manifiestos ni ejecuta el scraping completo.

### `POST /v1/consultas`

Inicia una consulta TICA.

Request:

```json
{
  "manifiesto": "ENGB2600229",
  "fecha_fin": "2026-07-13"
}
```

Reglas de entrada:

- Ambos campos son obligatorios.
- `manifiesto` no puede estar vacio.
- `fecha_fin` usa el formato ISO `YYYY-MM-DD`.
- No se acepta una modalidad elegida por el usuario.
- Los campos adicionales son rechazados.

Una entrada invalida devuelve HTTP 422 antes de abrir el navegador.

## 8. Probar desde PowerShell

Health del servicio:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/v1/health"
```

Consulta:

```powershell
$body = @{
    manifiesto = "ENGB2600229"
    fecha_fin = "2026-07-13"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/v1/consultas" `
    -ContentType "application/json" `
    -Body $body
```

El caracter de acento grave al final de una linea permite continuar un comando de PowerShell en la linea siguiente.

## 9. Estados de respuesta

Los resultados de negocio normalmente usan HTTP 200. El consumidor debe revisar el campo `estado`.

| Estado | Significado general |
|---|---|
| `ok` | Consulta completada |
| `pending` | Informacion final aun no disponible |
| `stale` | Se entrega una lectura anterior desde cache |
| `unavailable` | TICA o el navegador no estan disponibles |
| `needs_review` | Existe una seleccion ambigua |
| `not_found` | No se encontro el manifiesto |
| `not_implemented` | El flujo de modalidad aun no fue migrado |

El catalogo puede ampliarse o cambiar en futuras versiones del contrato. Los consumidores no deben asumir que HTTP 200 significa necesariamente `ok`.

## 10. Estado actual de la implementacion

FastAPI, la validacion, los health checks, el orquestador, el logging y la deteccion de modalidad ya estan implementados.

La consulta real puede:

1. Recibir y validar `manifiesto` y `fecha_fin`.
2. Abrir TICA mediante Playwright.
3. Buscar el conocimiento.
4. Leer Master.
5. Determinar si corresponde aereo o maritimo.

Los recorridos completos todavia deben migrarse desde la PoC:

- Sprint 2: flujo aereo.
- Sprint 3: flujo maritimo.

Hasta completar esos sprints, una consulta encontrada puede responder `not_implemented` despues de detectar su modalidad. Esto no afecta los health checks ni la validacion HTTP.

## 11. Ejecutar las pruebas

Las pruebas HTTP no consultan TICA vivo:

```powershell
& ".venv\Scripts\python.exe" -m pytest
& ".venv\Scripts\python.exe" -m ruff check app tests
& ".venv\Scripts\python.exe" -m mypy app tests
```

La suite verifica, entre otros puntos:

- Entrada valida e invalida.
- Respuesta HTTP 422.
- Health 200 y portal health 200/503.
- Serializacion de los estados.
- Contrato OpenAPI.
- Tipos enteros para `bultos` y `peso_bruto`.

## 12. Configuracion

La configuracion se define mediante variables con prefijo `TICA_`. Los valores de ejemplo estan en `.env.example`.

Ejemplos:

```text
TICA_API_PREFIX=/v1
TICA_LOG_LEVEL=INFO
TICA_BROWSER_HEADLESS=true
TICA_BROWSER_TIMEOUT_MS=30000
```

No se debe subir el archivo `.env` si contiene configuracion privada.

## 13. Ejecucion en produccion

La forma definitiva de ejecutar y desplegar el servicio se definira junto con la infraestructura de produccion. En Windows, el comando local vigente se ejecuta sin `--reload` para mantener compatibilidad con Playwright.

Antes de considerarlo listo para uso productivo deben estar completos, al menos:

- Flujo aereo de Sprint 2.
- Flujo maritimo de Sprint 3.
- Validaciones QA correspondientes.
- Configuracion del proceso, red, timeouts y monitoreo del ambiente destino.

FastAPI ya esta operativo como capa HTTP, pero el microservicio completo no debe considerarse terminado hasta migrar y validar los flujos del scraper.
