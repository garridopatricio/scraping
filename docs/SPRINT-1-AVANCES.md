# Sprint 1 - Infra base - Seguimiento de avances

Documento vivo para registrar el avance del Sprint 1 del proyecto Dokka Scrapping.

## Estado general

| Dato | Estado |
|---|---|
| Sprint | Sprint 1 - Infra base |
| Hito de salida | M1 - Infra lista y contrato API revisado |
| Estado | Completado - Hito M1 aprobado |
| Avance | 9 de 9 tareas completadas |
| Fecha de inicio del seguimiento | 2026-07-13 |
| Ultima actualizacion | 2026-07-13 |
| Ubicacion del proyecto | `scrapping-tica/` |
| Entorno virtual vigente | `scrapping-tica/.venv/` (excluido de Git) |
| Fuente principal | `Tareas_Dokka_Scrapping.md` |
| Prerrequisito | Sprint 0 / Gate M0 cerrado |
| Estimacion informada | 34 h, independiente de las estimaciones del backlog |

## Situacion actual

Estamos en **Sprint/Fase 1 - Infra base**. Esta fase prepara la arquitectura productiva alrededor de las reglas que ya fueron validadas en la PoC; no busca volver a crear el scraping aereo y maritimo desde cero.

Estado al 2026-07-13:

- **Completado:** TICA-010, scaffold y configuracion del proyecto.
- **Completado y corregido:** TICA-011, modelos Pydantic y enums alineados con la entrada real.
- **Base productiva extraida:** busqueda inicial, clasificacion y CAPTCHA viven en `app/scraper/domain.py`, `portal.py` y `captcha.py`, sin importar la PoC.
- **Completado:** TICA-012, gestor de navegador Playwright con serializacion, reintentos y backoff.
- **Completado:** TICA-013, clasificacion automatica e interfaz de estrategias aereo/maritimo.
- **Completado:** TICA-015, cache de ultima lectura buena con TTL.
- **Completado:** TICA-014, orquestador de consultas y degradacion con cache.
- **Completado:** TICA-016, logging estructurado JSON integrado al orquestador.
- **Completado:** TICA-017, API FastAPI y health checks.
- **Completado:** TICA-018, contrato aprobado y hito M1 cerrado.
- **Siguiente fase:** Sprint 2, modalidad aerea; TICA-020 fixtures en inicio.

La entrada vigente es `manifiesto` + `fecha_fin`. El usuario no selecciona modalidad. El codigo productivo busca el conocimiento, lee Master y clasifica internamente como aereo o maritimo. Terrestre no forma parte del alcance actual.

## Definicion de la Fase 1

El objetivo de esta fase es transformar la PoC validada en una base mantenible y preparada para API:

1. Mantener las reglas confirmadas del Sprint 0 como fuente funcional.
2. Definir un contrato tipado para entrada, estados y los 10 campos de salida.
3. Encapsular Playwright para no abrir navegadores sin control ni ejecutar consultas simultaneas agresivas.
4. Separar clasificacion, navegacion, orquestacion, cache y logging.
5. Exponer finalmente el servicio mediante FastAPI y revisar su contrato.

La Fase 1 termina en el hito **M1 - Infra lista**. Sprint 2 y Sprint 3 migraran respectivamente los flujos aereo y maritimo desde la PoC hacia estrategias productivas, sin duplicar las reglas existentes.

## Punto de partida confirmado

El Sprint 0 quedo cerrado favorablemente. La PoC comprobo que el portal publico de TICA permite consultar los datos requeridos para los flujos aereo y maritimo sin login ni CAPTCHA, incluyendo el DUA de nacionalizacion cuando existe y puede confirmarse.

El Sprint 1 comenzo sin estructura productiva. TICA-010 creo `pyproject.toml`, `.env.example`, `app/`, `tests/` y la configuracion base. Las reglas compartidas necesarias se extraen a modulos productivos; la PoC completa queda solo como referencia local en `tools/poc_validacion.py`, fuera del paquete y excluida de Git.

## Decisiones de Sprint 0 que condicionan este sprint

- El contrato actual contiene 10 campos: `fecha_arribo`, `transportista`, `movimiento_inventario`, `almacen_fiscal`, `fecha_ingreso_regimen`, `fecha_movimiento_inventario`, `bultos`, `peso_bruto`, `dua_nacionalizacion` y `fecha_dua`.
- `partidas_arancelarias` y `valor_aduanas_impuestos` fueron retirados del alcance y no deben ser campos requeridos del contrato actual.
- No se deben inventar datos. Las ausencias y fallos se expresan mediante estados normalizados.
- Estados del proyecto: `ok`, `pending`, `stale`, `unavailable`, `needs_review`, `not_found` y `not_implemented`.
- La entrada inicial no pide modalidad: recibe `manifiesto` y `fecha_fin`.
- La modalidad se detecta despues de buscar el conocimiento y leer `Desc Descarga` en Master: Caldera, Moin o Puerto Limon indican maritimo; otras descargas indican aereo.
- Terrestre queda fuera del alcance actual y no se intenta detectar ni despachar.
- La cedula maritima usada para filtrar Depositos permanece como configuracion interna del flujo, no como selector de modalidad del usuario.
- El DUA de movilizacion maritimo es interno y no puede devolverse como `dua_nacionalizacion`, salvo la excepcion confirmada para pedidos anticipados.
- Si una seleccion es ambigua, el servicio debe responder `needs_review` en vez de adivinar.
- La ventana maxima de consulta es de 15 dias.
- Un CAPTCHA no se resuelve: debe producir `unavailable` con motivo `captcha_required`.

## Resumen de los puntos del Sprint 1

| ID | Punto | Resultado esperado | Estado |
|---|---|---|---|
| TICA-010 | Scaffold microservicio Python | Proyecto instalable, configurable e importable | Completada |
| TICA-011 | Modelos Pydantic y enums | Contrato de entrada, salida y estados | Completada |
| TICA-012 | Gestor navegador con backoff | Navegador async, serializado y tolerante a fallos | Completada |
| TICA-013 | Interfaz estrategia modalidad | Clasificacion automatica y contrato comun aereo/maritimo | Completada |
| TICA-014 | Orquestador de consultas | Validacion, despacho, cache, reintentos y estados | Completada |
| TICA-015 | Cache ultima lectura buena | Soporte para respuestas `stale` con TTL | Completada |
| TICA-016 | Logging estructurado | Trazabilidad JSON sin datos sensibles | Completada |
| TICA-017 | API FastAPI y health | API inicial y pruebas de humo | Completada |
| TICA-018 | Revision contrato API | Hito M1 revisado y aprobado | Completada |

## Orden de trabajo sugerido

1. TICA-010 - Crear la base del proyecto.
2. TICA-011, TICA-012 y TICA-016 - Construir modelos, navegador y observabilidad sobre el scaffold.
3. TICA-013 y TICA-015 - Definir estrategias y cache.
4. TICA-014 - Integrar las piezas en el orquestador.
5. TICA-017 - Exponer la API y health checks.
6. TICA-018 - Revisar el contrato y cerrar M1.

## Seguimiento por tarea

### TICA-010 - Scaffold microservicio Python

**Estado:** Completada el 2026-07-13  
**Estimacion:** 4 h  
**Dependencia:** Gate M0 cerrado  
**Objetivo:** crear la estructura productiva del microservicio y su configuracion base.

Entregables previstos:

- `pyproject.toml`.
- `.env.example` sin secretos.
- Estructura de paquetes bajo `app/`.
- `app/config.py` con configuracion tipada.
- Dependencias base: Python 3.12, FastAPI, Pydantic v2, pydantic-settings, Playwright, structlog, pytest y pytest-asyncio.

Checklist:

- [x] Crear estructura de directorios y paquetes.
- [x] Declarar dependencias de ejecucion y desarrollo.
- [x] Crear configuracion basada en variables de entorno.
- [x] Verificar instalacion del proyecto.
- [x] Verificar que `app` importa sin errores.
- [x] Registrar comandos y resultados en Evidencias.

### TICA-011 - Modelos Pydantic y enums

**Estado:** Completada el 2026-07-13  
**Estimacion:** 4 h  
**Dependencia:** TICA-010  
**Objetivo:** definir el contrato de dominio alineado con las decisiones finales de la PoC.

Entregables previstos:

- `app/models/enums.py`.
- `app/models/shipment.py`.
- Modelos de entrada, resultado y datos por momento.
- Los siete estados normalizados.

Checklist:

- [x] Definir modalidades y estados.
- [x] Definir entrada unica por manifiesto y fecha fin, sin modalidad elegida por el usuario.
- [x] Incorporar los 10 campos vigentes del contrato.
- [x] Excluir como requeridos `partidas_arancelarias` y `valor_aduanas_impuestos`.
- [x] Diferenciar DUA de movilizacion interno y DUA de nacionalizacion de salida.
- [x] Agregar validaciones y pruebas de serializacion.

### TICA-012 - Gestor navegador con backoff

**Estado:** Completada el 2026-07-13  
**Estimacion:** 6 h  
**Dependencia:** TICA-010  
**Objetivo:** administrar Chromium de forma asincrona y segura frente a timeouts o caidas del portal.

Entregable previsto: `app/scraper/browser.py`.

Checklist:

- [x] Implementar context manager async.
- [x] Permitir headless configurable.
- [x] Serializar las consultas para evitar paralelismo agresivo contra TICA.
- [x] Implementar reintentos limitados con backoff.
- [x] Convertir fallos agotados en señal controlada de indisponibilidad.
- [x] Detectar CAPTCHA sin intentar resolverlo.
- [x] Probar con navegador o pagina simulada.

### TICA-013 - Interfaz estrategia modalidad

**Estado:** Completada el 2026-07-13  
**Estimacion:** 2 h  
**Dependencia:** TICA-011  
**Objetivo:** establecer una interfaz comun para que el orquestador despache por modalidad.

Entregables previstos:

- `app/scraper/base.py`.
- Clasificador productivo y contratos de estrategia en `aereo.py` y `maritimo.py`.

Checklist:

- [x] Definir `EstrategiaModalidad` asincrona.
- [x] Crear los puntos de extension aereo y maritimo sin dependencia de ejecucion sobre la PoC.
- [x] Reutilizar la modalidad detectada por `buscar_conocimiento` para el despacho automatico.
- [x] Verificar que no se solicite modalidad al usuario.
- [x] Verificar que terrestre no forme parte del despacho actual.

### TICA-014 - Orquestador de consultas

**Estado:** Completada el 2026-07-13  
**Estimacion:** 8 h  
**Dependencias:** TICA-011, TICA-013 y TICA-015  
**Objetivo:** centralizar validacion, seleccion de estrategia, ventana temporal, cache, reintentos y estados.

Entregable previsto: `app/orchestrator/consulta.py`.

Checklist:

- [x] Validar la entrada antes de abrir el navegador.
- [x] Exigir manifiesto y fecha fin, sin pedir modalidad.
- [x] Aplicar ventana maxima de 15 dias.
- [x] Buscar primero el conocimiento y despachar segun la modalidad detectada en Master.
- [x] Integrar cache y ultima lectura buena.
- [x] Mapear timeout/caida con cache a `stale`.
- [x] Mapear timeout/caida sin cache a `unavailable`.
- [x] Mapear CAPTCHA a `unavailable/captcha_required`.
- [x] Reservar `needs_review` para resultados ambiguos.
- [x] Cubrir cada rama con dependencias simuladas.

### TICA-015 - Cache ultima lectura buena

**Estado:** Completada el 2026-07-13  
**Estimacion:** 3 h  
**Dependencia:** TICA-011  
**Objetivo:** conservar el ultimo resultado valido para degradacion controlada.

Entregable previsto: `app/cache/store.py`.

Checklist:

- [x] Definir interfaz desacoplada del almacenamiento.
- [x] Implementar cache en memoria.
- [x] Usar clave por modalidad e identificador.
- [x] Implementar TTL.
- [x] Probar guardado, recuperacion y expiracion.
- [x] Mantener una interfaz migrable a Redis.

### TICA-016 - Logging estructurado

**Estado:** Completada el 2026-07-13  
**Estimacion:** 1 h  
**Dependencia:** TICA-010  
**Objetivo:** registrar cada consulta de forma estructurada y util para soporte.

Entregable previsto: `app/observability/logging.py`.

Checklist:

- [x] Configurar structlog con salida JSON.
- [x] Registrar modalidad, estado y duracion.
- [x] Incorporar un identificador de correlacion generado por consulta.
- [x] Evitar credenciales, manifiesto, payload y datos sensibles innecesarios.
- [x] Verificar una salida representativa y la integracion con el orquestador.

### TICA-017 - API FastAPI y health

**Estado:** Completada el 2026-07-13  
**Estimacion:** 2 h  
**Dependencia:** TICA-014  
**Objetivo:** exponer el contrato inicial que consumira RAGA Orders.

Entregables previstos:

- `app/api/routes.py`.
- `app/main.py`.
- `tests/test_api.py`.

Checklist:

- [x] Crear `POST /v1/consultas`.
- [x] Crear `GET /v1/health`.
- [x] Crear `GET /v1/health/portal`.
- [x] Verificar respuesta 422 para entrada invalida sin invocar el orquestador.
- [x] Verificar health 200 y portal health 200/503.
- [x] Probar que los siete estados se serializan correctamente.
- [x] Documentar el comando de inicio, rutas y ejemplos de request/response.

### TICA-018 - Revision contrato API

**Estado:** Completada y aprobada el 2026-07-13  
**Estimacion:** 2 h  
**Dependencia:** TICA-017  
**Objetivo:** validar payloads, errores, estados y compatibilidad antes de los flujos aereo y maritimo.

Checklist:

- [x] Revisar entrada unica por manifiesto y fecha fin.
- [x] Revisar los 10 campos de salida vigentes.
- [x] Confirmar que los campos retirados no sean obligatorios.
- [x] Revisar los siete estados y sus motivos.
- [x] Revisar ejemplos de error, timeout, CAPTCHA y ambiguedad.
- [x] Registrar observaciones y decisiones en `docs/SPRINT-1-CONTRATO-API.md`.
- [x] Obtener aprobacion del hito M1.

## Preguntas y riesgos heredados de Sprint 0

Estas preguntas no bloquean el scaffold, pero deben resolverse o reflejarse correctamente en el contrato antes de cerrar M1:

- [ ] Confirmar si produccion recibira cedula juridica completa o permitira cedula parcial.
- [ ] Definir la segunda regla cuando exista mas de un movimiento `ING` para la misma cedula.
- [ ] Definir los campos operativos que se mostraran para conocimientos con varias lineas.
- [ ] Definir como elegir el DUA correcto cuando existan varios DUAs asociados.
- [ ] Confirmar la salida de bultos y peso en pedidos maritimos anticipados sin otra fuente final.

Mientras una regla siga abierta, el contrato debe permitir una respuesta segura como `needs_review` o `pending`, sin seleccionar datos por suposicion.

## Definicion de terminado para cada tarea

Una tarea solo puede marcarse como completada cuando:

- [ ] El codigo es asincrono y tipado donde corresponde.
- [ ] Los tests relevantes estan en verde y no consultan TICA en vivo.
- [ ] No hay errores evidentes de tipo o lint.
- [ ] Los contratos o decisiones modificados quedan documentados.
- [ ] No se incluyen secretos ni datos sensibles innecesarios.
- [ ] Se registra evidencia verificable en este documento.

## Criterios de cierre del Sprint 1 / Hito M1

- [x] Las nueve tareas estan completadas.
- [x] El proyecto se instala e importa correctamente.
- [x] Los modelos representan el contrato vigente de 10 campos.
- [x] Los siete estados estan definidos y probados.
- [x] El navegador tiene reintentos, backoff y ejecucion serializada.
- [x] El orquestador valida antes de navegar e integra cache.
- [x] La API y ambos health checks responden correctamente.
- [x] Los tests de Sprint 1 estan en verde sin tocar TICA en vivo.
- [x] El contrato API fue revisado y aprobado.

## Registro de avances

Agregar una fila por cada cambio relevante.

| Fecha | Tarea | Avance | Evidencia | Estado resultante |
|---|---|---|---|---|
| 2026-07-13 | Sprint 1 | Se crea documento de seguimiento; se verifica que la estructura productiva aun no existe. | Revision local de rutas previstas | Por iniciar |
| 2026-07-13 | TICA-010 | Se crea el scaffold, configuracion tipada, dependencias y pruebas de humo. | Instalacion editable correcta; 4 tests, Ruff y mypy en verde | Completada |
| 2026-07-13 | Estructura | Se agrupa el codigo y seguimiento del Sprint 1 dentro de `scrapping-tica/`. | Verificacion de rutas y nueva ejecucion desde la subcarpeta | En curso |
| 2026-07-13 | Documentacion | Se crea `docs/` y se reubican el cierre de Sprint 0 y el seguimiento de Sprint 1. | Indice documental y rutas de imagen corregidas | Completada |
| 2026-07-13 | TICA-011 | Se implementan enums, entrada, momentos 1-3, resultado publico y contexto maritimo interno. | 18 tests, Ruff y mypy en verde tras correccion de alcance | Completada |
| 2026-07-13 | Correccion de alcance | Se corrige la entrada para no pedir modalidad ni contemplar terrestre; las reglas validadas se identifican para migrarlas a produccion. | Pruebas sobre clasificacion confirmada | TICA-011 corregida |
| 2026-07-13 | TICA-012 | Se implementa gestor Playwright serializado con cierre seguro, reintentos, backoff y errores controlados. | 23 tests en verde y Chromium local abre `about:blank` | Completada |
| 2026-07-13 | TICA-013 | Se crean interfaz, puntos de extension y despachador aereo/maritimo. | Terrestre y modalidades desconocidas se rechazan | Completada |
| 2026-07-13 | TICA-015 | Se implementa cache en memoria de ultima lectura buena con TTL e interfaz reemplazable. | 36 tests en verde; expiracion, aislamiento y claves aprobados | Completada |
| 2026-07-13 | TICA-014 | Se integran entrada, navegador, busqueda, modalidad detectada, estrategias, mapeo de datos y cache. | 43 tests en verde; estados y ventana de 15 dias aprobados | Completada |
| 2026-07-13 | Estructura GitHub | Se crea un entorno virtual local dentro de `scrapping-tica/` sin eliminar el anterior. | 43 tests, Ruff y mypy ejecutados con el nuevo `.venv` | Completada |
| 2026-07-13 | Correccion de arquitectura | Se extraen busqueda, clasificacion y CAPTCHA a codigo productivo; la PoC sale de `app/` y no sera dependencia del servicio. | 48 tests; cero imports de `poc_validacion` en `app/` y `tests/`; Ruff y mypy en verde | Completada |
| 2026-07-13 | TICA-016 | Se configura structlog JSON y se registra una linea por consulta con correlacion, modalidad, estado y duracion, sin manifiesto. | 51 tests; salida JSON e integracion con orquestador verificadas; Ruff y mypy en verde | Completada |
| 2026-07-13 | TICA-017 | Se crea FastAPI con consulta, health de servicio y health real de conectividad al portal. | 63 tests; entrada invalida 422, health 200/503 y siete estados serializados; Ruff y mypy en verde | Completada |
| 2026-07-13 | TICA-018 | Se revisa OpenAPI contra Sprint 0, se documentan payloads, estados y errores, y se agrega 503 al contrato de portal health. | `docs/SPRINT-1-CONTRATO-API.md`; 67 tests; Ruff y mypy en verde | En revision |
| 2026-07-13 | TICA-018 / M1 | Se aprueba el contrato: cantidades enteras y decisiones por `estado`; se cierra Sprint 1. | 71 tests; contrato y seguimiento actualizados | Completada |
| 2026-07-13 | Correccion posterior a M1 | Se controla el event loop incompatible de Uvicorn `--reload` en Windows y se corrige el comando de ejecucion. | El portal health devuelve 503 en vez de 500; guia y README actualizados | Completada |

## Registro de decisiones

| Fecha | Decision | Motivo |
|---|---|---|
| 2026-07-13 | Se toma `Tareas_Dokka_Scrapping.md` como fuente principal del Sprint 1. | El archivo nuevo tiene preferencia para el seguimiento. |
| 2026-07-13 | Las 34 h se conservan como estimacion independiente. | No se comparan ni concilian con las horas del backlog. |
| 2026-07-13 | El contrato de Sprint 1 parte de los 10 campos confirmados en Sprint 0. | Partidas arancelarias y valor/impuestos fueron retirados del alcance. |
| 2026-07-13 | La estructura productiva de la fase se mantiene bajo `scrapping-tica/`. | Separa el desarrollo productivo de la PoC y de los documentos generales del proyecto. |
| 2026-07-13 | Los documentos del proyecto viven bajo `scrapping-tica/docs/`. | Centraliza documentos vivos, cierres e indices. |
| 2026-07-13 | El DUA de movilizacion se modela en `ContextoMaritimo`, fuera de `ResultadoTICA`. | Evita publicarlo accidentalmente como DUA de nacionalizacion. |
| 2026-07-13 | El usuario entrega manifiesto y fecha fin; no selecciona modalidad. | El clasificador productivo usa `Desc Descarga` en Master antes de despachar el flujo. |
| 2026-07-13 | Terrestre queda fuera del contrato y del despacho actual. | El alcance vigente solo usa aereo y maritimo; una ampliacion futura requerira una decision nueva. |
| 2026-07-13 | La PoC se conserva solo como referencia local en `tools/poc_validacion.py` y se excluye de Git. | El futuro API/microservicio debe desplegarse sin el archivo de validacion. |
| 2026-07-13 | Ningun modulo de `app/` puede importar la PoC. | Las reglas reutilizables se copian y adaptan a modulos productivos con pruebas propias. |
| 2026-07-13 | Los flujos completos aereo y maritimo permanecen marcados como no migrados. | Su migracion corresponde a Sprint 2 y Sprint 3; Sprint 1 solo prepara la infraestructura y el despacho. |
| 2026-07-13 | `ResultadoTICA.modalidad` permite `null` antes de la clasificacion. | Si TICA falla antes de leer Master, no corresponde inventar si el manifiesto es aereo o maritimo. |
| 2026-07-13 | La ventana enviada a TICA incluye fecha fin y los 14 dias anteriores. | Cumple el tope de 15 dias definido para la consulta productiva. |
| 2026-07-13 | El entorno de trabajo vigente vive en `scrapping-tica/.venv/`. | Deja el servicio autocontenido localmente; `.venv/` permanece fuera de Git mediante `.gitignore`. |
| 2026-07-13 | Se ignoran salidas y capturas locales de la PoC. | Evita subir por accidente resultados o evidencias potencialmente sensibles a GitHub. |
| 2026-07-13 | El log operativo no incluye manifiesto ni payload de entrada/salida. | Para soporte bastan correlacion, modalidad, estado y duracion; se minimiza la exposicion de datos. |
| 2026-07-13 | Cada consulta genera internamente un `correlacion_id`. | Permite seguir un evento sin usar el manifiesto como identificador de log. |
| 2026-07-13 | `app/main.py` solo crea y configura FastAPI; no contiene reglas de scraping. | La navegacion y el negocio permanecen en portal, estrategias y orquestador. |
| 2026-07-13 | El orquestador y la cache se reutilizan entre requests mediante una dependencia compartida. | Evita perder la ultima lectura buena al crear una instancia nueva por solicitud. |
| 2026-07-13 | `/health/portal` comprueba solo la portada de TICA y devuelve 503 si no responde. | Distingue salud del proceso y disponibilidad externa sin consultar manifiestos. |
| 2026-07-13 | Los fallos de validacion usan HTTP 422; los resultados de negocio usan HTTP 200 con `estado` y `motivo`. | Separa errores del payload de estados propios de la consulta TICA. Aprobado en M1. |
| 2026-07-13 | La indisponibilidad de `/health/portal` se documenta tambien como HTTP 503 en OpenAPI. | El contrato debe reflejar el comportamiento real del endpoint. |
| 2026-07-13 | `bultos` y `peso_bruto` son enteros; el punto de TICA es separador de miles. | `3.000` representa `3000`, no el decimal `3`. |
| 2026-07-13 | RAGA y otros consumidores deciden por `estado`; el catalogo podra evolucionar. | Nuevos estados o cambios se incorporaran posteriormente mediante una actualizacion del contrato. |
| 2026-07-13 | Uvicorn se ejecuta sin `--reload` en el desarrollo local de Windows. | La recarga activa un event loop que no soporta el subproceso requerido por Playwright. |

## Evidencias y comandos de verificacion

Registrar aqui los comandos ejecutados y una sintesis del resultado, evitando copiar salidas extensas.

| Fecha | Tarea | Verificacion | Resultado |
|---|---|---|---|
| 2026-07-13 | Inicio | Existencia de `pyproject.toml`, `.env.example`, `app/` y `tests/` | No existen; Sprint 1 inicia desde cero |
| 2026-07-13 | TICA-010 | `.venv\\Scripts\\python.exe -m pip install -e ".[dev]"` | Proyecto instalado correctamente en modo editable |
| 2026-07-13 | TICA-010 | `.venv\\Scripts\\python.exe -m pytest` | 4 pruebas aprobadas |
| 2026-07-13 | TICA-010 | `.venv\\Scripts\\python.exe -m ruff check app tests` | Sin observaciones |
| 2026-07-13 | TICA-010 | `.venv\\Scripts\\python.exe -m mypy app tests` | Sin errores en 10 archivos fuente |
| 2026-07-13 | TICA-010 | Importar `app` y cargar `get_settings()` | Version 0.1.0, configuracion cargada y ventana maxima de 15 dias |
| 2026-07-13 | Estructura | Reinstalar desde `scrapping-tica/` y repetir pytest, Ruff, mypy e importacion | 4 tests aprobados; lint y tipado limpios; `app` carga desde `scrapping-tica/app` |
| 2026-07-13 | Documentacion | Verificar documentos movidos y referencias de imagen | `docs/README.md`, cierre Sprint 0 y seguimiento Sprint 1 disponibles; imagenes apuntan a `../../evidencias` |
| 2026-07-13 | TICA-011 | `.venv\\Scripts\\python.exe -m pytest` | 18 pruebas aprobadas, incluidas reglas de clasificacion de la PoC |
| 2026-07-13 | TICA-011 | Ruff y mypy sobre codigo productivo y tests | Sin observaciones en el alcance implementado |
| 2026-07-13 | TICA-012 | Pruebas de gestor con Playwright simulado | Apertura/cierre, timeout, backoff, agotamiento, serializacion y CAPTCHA aprobados |
| 2026-07-13 | TICA-012 | Prueba local de Chromium con `about:blank` | `BROWSER_OK`; no se consulto TICA |
| 2026-07-13 | TICA-012 | Pytest, Ruff y mypy | 23 pruebas aprobadas; lint y tipado sin errores en codigo productivo |
| 2026-07-13 | TICA-013 | Pruebas de estrategias y despacho | Seleccion aereo/maritimo, rechazo de terrestre y estado explicito para flujos aun no migrados aprobados |
| 2026-07-13 | TICA-013 | Pytest, Ruff y mypy | 30 pruebas aprobadas; lint limpio y tipado sin errores en 20 archivos fuente |
| 2026-07-13 | TICA-015 | Pruebas de cache | Solo guarda `ok`; recuperacion, TTL, reemplazo, aislamiento, eliminacion y limpieza aprobados |
| 2026-07-13 | TICA-015 | Pytest, Ruff y mypy | 36 pruebas aprobadas; lint limpio y tipado sin errores en 22 archivos fuente |
| 2026-07-13 | TICA-014 | Pruebas del orquestador | `ok`, `pending`, `not_found`, `needs_review`, `unavailable`, `stale`, cache y ventana aprobados |
| 2026-07-13 | TICA-014 | Pytest, Ruff y mypy | 43 pruebas aprobadas; lint limpio y tipado sin errores en 24 archivos fuente |
| 2026-07-13 | Estructura GitHub | `.venv\\Scripts\\python.exe` ejecuta pytest, Ruff y mypy | 43 pruebas aprobadas; entorno original superior confirmado intacto |
| 2026-07-13 | Correccion de arquitectura | Pytest, Ruff, mypy y busqueda de imports de la PoC | 48 pruebas aprobadas; lint y tipado limpios en 28 archivos; sin dependencia de la PoC en produccion o tests |
| 2026-07-13 | TICA-016 | `.venv\\Scripts\\python.exe` ejecuta pytest, Ruff y mypy | 51 pruebas aprobadas; lint y tipado limpios en 30 archivos fuente |
| 2026-07-13 | TICA-016 | Captura y parseo de la salida de structlog | JSON valido con `correlacion_id`, `modalidad`, `estado`, `duracion_ms`, nivel y timestamp; sin manifiesto |
| 2026-07-13 | TICA-017 | `.venv\\Scripts\\python.exe` ejecuta pytest, Ruff y mypy | 63 pruebas aprobadas sin warnings; lint y tipado limpios en 33 archivos fuente |
| 2026-07-13 | TICA-017 | Pruebas HTTP con transporte ASGI, sin levantar red ni consultar TICA | POST valido/422, health 200, portal 200/503 y los siete estados aprobados |
| 2026-07-13 | TICA-018 | Pruebas del esquema OpenAPI | Entrada exacta, 10 campos, campos retirados ausentes, siete estados y respuesta 503 documentada |
| 2026-07-13 | TICA-018 | Pytest, Ruff y mypy | 67 pruebas aprobadas; lint y tipado limpios; sin consultas a TICA vivo |
| 2026-07-13 | TICA-018 / M1 | Pruebas de cantidades y contrato final | 71 pruebas aprobadas; `3.000`, `614.000` y `7450.000` convertidos a enteros; OpenAPI publica tipo integer |
| 2026-07-13 | Correccion health portal | Reproduccion con event loop selector, Pytest, Ruff y mypy | Devuelve indisponibilidad controlada sin iniciar Playwright; 72 pruebas aprobadas, lint y tipado limpios |
