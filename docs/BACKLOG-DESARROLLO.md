# Backlog de desarrollo — Integración TICA → RAGA Orders

> Tickets técnicos para el desarrollador. Derivado de `PLANIFICACION-PM-NOTION.md`.
> Normativa del proyecto en `CLAUDE.md`; detalle de diseño en `ESPECIFICACION-TECNICA-TICA.md`.
> Convención: identificadores y rutas en inglés; comentarios y docs en español. Todo async.

## Cómo usar este documento

Cada ticket es una unidad de trabajo autocontenida. El flujo por ticket es:
leer el ticket → pasar el contexto a Claude Code → revisar → correr tests → commit → cerrar.
No abrir una fase sin cerrar la anterior (regla del proyecto).

### Definición de Terminado (DoD) — aplica a TODOS los tickets

Un ticket está terminado solo si:
1. El código sigue las convenciones del `CLAUDE.md` (async, tipado, comentarios en español).
2. Los tests corren en verde **contra fixtures**, nunca contra TICA en vivo.
3. No hay errores de tipo ni lint evidentes.
4. Si cambió el contrato de datos o la API, se actualizó la especificación técnica.
5. Commit con mensaje claro y push a la rama del ticket.

### Leyenda de estados de salida (modelo del proyecto)
`ok · pending · stale · unavailable · needs_review · not_found · not_implemented`

---

# FASE 0 — PoC de validación (GATE)

## TICA-001 · Script de PoC de validación · 6 h
**Depende de:** caso real solicitado a Dökka
**Archivo:** `scripts/poc_validacion.py`

**Alcance:** script desechable (no producción) que navega el portal externo
`https://portaltica.hacienda.go.cr/TicaExterno/` con Playwright (Chromium, headless desactivable)
y verifica, para un caso aéreo y uno marítimo pasados por variables de entorno, qué campos se obtienen
sin login ni CAPTCHA.

**Notas técnicas:**
- Recorrer para aéreo: consulta por conocimiento → Líneas y Afectaciones → DUAs.
- Recorrer para marítimo: conocimiento → Líneas y Afectaciones → Depósitos → Movimientos por Nº Inventario.
- En cada pantalla registrar: ¿pidió login?, ¿apareció CAPTCHA?, ¿qué campos de los 12 son visibles?
- Si aparece un CAPTCHA: **detener y registrar**, nunca intentar resolverlo.

**Criterios de aceptación:**
- Corre con parámetros por entorno, sin credenciales hardcodeadas.
- No inventa datos: si algo no carga, lo marca como no disponible.
- Genera `poc_resultado.md` con tabla `campo | visible sí/no | requiere login sí/no | observaciones`.

## TICA-002 · Ejecutar PoC y documentar hallazgos · 4 h
**Depende de:** TICA-001 + caso real recibido
**Salida:** `poc_resultado.md` (queda fuera de git por `.gitignore`)

**Alcance:** correr la PoC con los casos reales de Dökka y completar el reporte de los 12 campos.

**Criterios de aceptación:**
- Los 12 campos quedan clasificados como públicos o con login.
- Queda explícito el estado del campo crítico *valor de aduanas / impuestos*.
- Handoff a QA para revisión contra el documento de proceso de Dökka.

> **GATE M0:** este ticket define mejor caso (136 h) vs. peor caso (168 h). No se cotiza en firme antes de cerrarlo.

---

# FASE 1 — Infra base

## TICA-010 · Scaffold del repositorio + configuración · 4 h
**Depende de:** F0
**Archivos:** `pyproject.toml`, `.env.example`, estructura de `app/`, `app/config.py`

**Alcance:** crear la estructura de la sección 2 de la especificación y las dependencias
(Python 3.12, fastapi, pydantic v2, pydantic-settings, playwright, structlog, pytest, pytest-asyncio).
`config.py` con `Settings` basado en pydantic-settings.

**Criterios de aceptación:** `pip install -e .` (o `uv sync`) funciona; `app` importa sin error;
`.env.example` lista todas las variables.

## TICA-011 · Modelos Pydantic · 4 h
**Depende de:** TICA-010
**Archivos:** `app/models/enums.py`, `app/models/shipment.py`

**Alcance:** implementar TODOS los modelos de la sección 3 de la especificación tal cual
(`Modalidad`, `EstadoConsulta`, `ConsultaInput`, `DatosMomento1/2/3`, `PartidaArancelaria`, `ResultadoTICA`).

**Criterios de aceptación:** modelos validan y serializan; `EstadoConsulta` cubre los 7 estados;
`ConsultaInput` acepta los tres identificadores (conocimiento / codigo_dms / cedula_juridica).

## TICA-013 · Gestor de navegador Playwright · 6 h
**Depende de:** TICA-010
**Archivo:** `app/scraper/browser.py`

**Alcance:** ciclo de vida de Chromium headless como context manager async, con **reintentos con backoff**
ante timeouts/caídas y **peticiones serializadas** (sin paralelismo agresivo contra el portal).

**Criterios de aceptación:** expone un context manager que entrega una página lista;
tras N fallos devuelve señal de indisponibilidad (no excepción cruda); test con navegador simulado en verde.

## TICA-014 · Interfaz de estrategia + stubs de modalidad · 2 h
**Depende de:** TICA-011
**Archivos:** `app/scraper/base.py`, `app/scraper/{aereo,maritimo,terrestre}.py`

**Alcance:** clase abstracta `EstrategiaModalidad` con `async consultar(input) -> ResultadoTICA`.
Crear los tres stubs: aéreo y marítimo con `NotImplementedError`; terrestre devuelve estado `not_implemented`.

**Criterios de aceptación:** el orquestador puede importar y despachar a cualquier estrategia;
terrestre responde `not_implemented` sin romper.

## TICA-015 · Orquestador de consultas · 8 h
**Depende de:** TICA-014, TICA-016
**Archivo:** `app/orchestrator/consulta.py`

**Alcance:** recibe `ConsultaInput`, **valida** (marítimo exige cédula; aéreo exige conocimiento;
terrestre exige codigo_dms), **calcula la ventana de fechas** (tope 15 días), elige la estrategia,
integra la caché, y **mapea excepciones/timeouts al modelo de estados** (sección 8 del CLAUDE.md).
Incluye la lógica de reintento por momento.

**Criterios de aceptación:**
- Entrada inválida → error de validación claro antes de tocar el navegador.
- Portal sin respuesta con caché → `stale`; sin caché → `unavailable`.
- CAPTCHA detectado → `unavailable` motivo `captcha_required`.
- Tests de cada rama de estado con dependencias simuladas.

## TICA-016 · Caché de última lectura buena · 3 h
**Depende de:** TICA-011
**Archivo:** `app/cache/store.py`

**Alcance:** caché en memoria por `(modalidad, identificador)` con TTL, con interfaz lista para
migrar a Redis después.

**Criterios de aceptación:** guarda/recupera `ResultadoTICA`; respeta TTL; interfaz desacoplada
de la implementación en memoria.

## TICA-017 · Logging estructurado · 1 h
**Depende de:** TICA-010
**Archivo:** `app/observability/logging.py`

**Alcance:** structlog en JSON + helper para loguear cada consulta (estado + duración).

**Criterios de aceptación:** cada consulta emite una línea JSON con modalidad, estado y duración.

## TICA-018 · API FastAPI + test de humo · 2 h
**Depende de:** TICA-015
**Archivos:** `app/api/routes.py`, `app/main.py`, `tests/test_api.py`

**Alcance:** endpoints `POST /v1/consultas`, `GET /v1/health`, `GET /v1/health/portal`.
Test mínimo de que la API levanta y valida la entrada.

**Criterios de aceptación:** `POST /v1/consultas` con entrada inválida devuelve 422;
health responde 200; test de humo en verde.

> **Hito M1 — Infra lista.** Handoff a QA para revisión del contrato de API.

---

# FASE 2 — Modalidad aérea

## TICA-020 · Grabar fixtures del flujo aéreo · 3 h
**Depende de:** F1 + caso real
**Ruta:** `tests/fixtures/aereo/`

**Alcance:** grabar el HTML real de cada pantalla del flujo aéreo (Momentos 1–3) como fixtures.

**Criterios de aceptación:** fixtures cubren un caso con arribo, uno sin arribo, y uno con
ambigüedad madre/hijo. Sin datos sensibles reales fuera de lo necesario.

## TICA-021 · Aéreo — Momento 1 (arribo) · 3 h
**Depende de:** TICA-020
**Archivo:** `app/scraper/aereo.py`

**Alcance:** consulta por conocimiento aéreo → `fecha_arribo` + `razon_social_transportista`.
Sin arribo → `pending`.

**Criterios de aceptación:** parsea contra fixture; caso sin arribo devuelve `pending`.

## TICA-022 · Aéreo — Momento 2 (regla ING + madre/hijo) · 6 h
**Depende de:** TICA-021
**Archivo:** `app/scraper/aereo.py`

**Alcance:** Líneas y Afectaciones → filtrar estado **ING** y elegir el **movimiento hijo** (no la madre).
Capturar movimiento, almacén fiscal, **fecha de ingreso al régimen Y fecha del movimiento** (ambas, no colapsar),
bultos, peso.

**Criterios de aceptación:**
- Ante ambigüedad madre/hijo → `needs_review` motivo `ambiguedad_madre_hijo` (nunca adivina).
- Captura las dos fechas por separado.

## TICA-023 · Aéreo — Momento 3 (DUA) · 3 h
**Depende de:** TICA-022
**Archivo:** `app/scraper/aereo.py`

**Alcance:** sección DUAs → nº DUA, fecha, partidas (tabla multilínea), valor/impuestos.
Sin DUA → `pending`.

**Criterios de aceptación:** parsea la tabla de partidas como lista; sin DUA devuelve `pending`.

## TICA-024 · Tests de la modalidad aérea · 3 h
**Depende de:** TICA-023
**Archivo:** `tests/test_aereo.py`

**Alcance:** tests contra fixtures: caso correcto, caso madre/hijo → `needs_review`, caso sin arribo → `pending`.

**Criterios de aceptación:** los tres casos en verde; ninguno toca TICA en vivo.

> **Hito M2 — Aéreo en verde.** Handoff a QA para validación con casos reales.

---

# FASE 3 — Modalidad marítima

## TICA-030 · Grabar fixtures del flujo marítimo · 4 h
**Depende de:** F1 + caso real con cédula
**Ruta:** `tests/fixtures/maritimo/`

**Alcance:** grabar HTML de los 9 pasos, incluyendo un consolidado con varias cédulas.

**Criterios de aceptación:** fixtures cubren el flujo completo y un consolidado multi-cédula.

## TICA-031 · Marítimo — pasos 1–2 (conocimiento + DUA movilización) · 6 h
**Depende de:** TICA-030
**Archivo:** `app/scraper/maritimo.py`

**Alcance:** conocimiento → arribo/transportista; Líneas y Afectaciones → identificar el
**DUA de movilización** (aduana, año, número, depósito destino). Marcarlo explícitamente como movilización.

**Criterios de aceptación:** el DUA de movilización queda en un campo interno claramente distinto
del de nacionalización.

## TICA-032 · Marítimo — pasos 3–5 (depósitos + filtro cédula) · 10 h
**Depende de:** TICA-031
**Archivo:** `app/scraper/maritimo.py`

**Alcance:** Depósitos → Movimientos por Número de Inventario (NO ir a DUAs directo) con depósito + fecha +
DUA de movilización → **filtrar por la cédula jurídica del input** dentro del consolidado → en Detenciones,
el movimiento de inventario real (movimiento, depósito, ambas fechas, bultos, peso).

**Criterios de aceptación:**
- Filtra correctamente por cédula sobre un consolidado multi-cédula (test dedicado).
- Si no encuentra la cédula → `not_found`, no devuelve el movimiento de otra empresa.

## TICA-033 · Marítimo — paso 6 (DUA nacionalización) + regla dura · 6 h
**Depende de:** TICA-032
**Archivo:** `app/scraper/maritimo.py`

**Alcance:** Duas del depósito → **DUA de nacionalización** y sus datos.
**Regla dura:** el DUA de movilización NUNCA se devuelve como `dua_nacionalizacion`.
Si no se llega a un DUA de nacionalización confirmado, ese campo queda `None` y el estado es `pending`.

**Criterios de aceptación:** imposible que `dua_nacionalizacion` contenga el de movilización (garantizado por test).

## TICA-034 · Tests de la modalidad marítima · 4 h
**Depende de:** TICA-033
**Archivo:** `tests/test_maritimo.py`

**Alcance:** caso completo correcto; **test crítico** que verifica que el DUA de movilización no se reporta
como nacionalización; caso consolidado multi-cédula que debe filtrar la correcta.

**Criterios de aceptación:** los tres casos en verde; el test crítico falla si alguien rompe la regla dura.

> **Hito M3 — Marítimo en verde.** Handoff a QA.

---

# FASE 4 — Módulo embarques RAGA Orders (repo RAGA, no el scraper)

> Contexto: Laravel 12 + Inertia 2 + React 19. Seguir `RAGA-CONVENTIONS.md` y las reglas de mutación/refresh.

## TICA-040 · Migración de campos de embarque · 4 h
**Depende de:** contrato de F1
**Alcance:** agregar `codigo_dms` (terrestre), `cedula_juridica` del importador, y soporte para
**múltiples conocimientos por embarque** (aéreo/marítimo).
**Criterios de aceptación:** migración reversible; modelo y factory actualizados; no rompe embarques existentes.

## TICA-041 · UI detalle de orden con datos TICA · 4 h
**Depende de:** TICA-040
**Alcance:** mostrar en el detalle de orden consolidada los campos que vienen de TICA (DUA, fecha liberación,
movimiento, almacén, bultos, peso, partidas, valor) con su **estado** (ok / pendiente / en revisión / no disponible).
**Criterios de aceptación:** cada campo muestra su estado; los `needs_review` se distinguen visualmente.

## TICA-042 · Cliente HTTP al servicio TICA · 4 h
**Depende de:** API de F1
**Alcance:** cliente que consume `POST /v1/consultas`, mapea los estados del contrato, y respeta el
**contrato de refresh** (tras consulta exitosa la vista refleja el dato sin recarga manual).
**Criterios de aceptación:** maneja los 7 estados; timeouts no rompen la vista; refresh sin recarga.

> **Hito M4 — Integración RAGA.**

---

# FASE 5 — QA integral (QA es dueño; el dev da soporte)

## TICA-050 · Test de degradación + CAPTCHA simulado · 3 h
**Depende de:** F2 + F3
**Archivo:** `tests/test_degradacion.py`

**Alcance (dev):** provocar con fixtures: portal caído → `stale` con caché / `unavailable` sin caché;
CAPTCHA en fixture → `unavailable` motivo `captcha_required` sin intentar resolverlo.

**Criterios de aceptación:** ambos escenarios en verde; el test de CAPTCHA falla si alguien intentara resolverlo.

## TICA-051 · Soporte a la matriz de estados de QA · 2 h
**Depende de:** F2 + F3
**Alcance (dev):** exponer hooks/fixtures que QA necesite para forzar cada uno de los 7 estados.
**Criterios de aceptación:** QA puede reproducir los 7 estados de forma determinística.

> **Hito M5 — QA integral cerrado** (matriz de estados y validación de reglas con casos reales:
> tareas propias de QA en `PLANIFICACION-PM-NOTION.md`).

---

# FASE 6 — Modalidad terrestre (CONDICIONAL)

> No iniciar sin la grabación del proceso real y la confirmación del formato del código DMS.

## TICA-060 · Grabar fixtures terrestre · 3 h
**Depende de:** grabación recibida
**Ruta:** `tests/fixtures/terrestre/`

## TICA-061 · Implementar terrestre.py · 12 h
**Depende de:** TICA-060
**Archivo:** `app/scraper/terrestre.py`
**Alcance:** mismo patrón de estrategia que aéreo/marítimo, entrada por código DMS.
Actualizar la especificación (sección 5.3) con el flujo confirmado.

## TICA-062 · Tests terrestre + validación · 5 h
**Depende de:** TICA-061
**Archivo:** `tests/test_terrestre.py`
**Alcance:** tests equivalentes a las otras modalidades; handoff a QA.

> **Hito M6 — Terrestre (condicional).**

---

## Resumen de esfuerzo por fase

| Fase | Tickets | Horas |
|---|---|---|
| F0 | TICA-001, 002 | 10 h dev (+2 h QA) |
| F1 | TICA-010 … 018 | 30 h |
| F2 | TICA-020 … 024 | 18 h dev (+4 h QA) |
| F3 | TICA-030 … 034 | 30 h dev (+4 h QA) |
| F4 | TICA-040 … 042 | 12 h |
| F5 | TICA-050, 051 (+ QA) | 5 h dev (+13 h QA) |
| F6 | TICA-060 … 062 | 20 h (condicional) |
