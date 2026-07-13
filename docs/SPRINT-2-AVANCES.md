# Sprint 2 - Modalidad aerea - Seguimiento de avances

Documento vivo para migrar el flujo aereo validado en la PoC hacia codigo productivo.

## Estado general

| Dato | Estado |
|---|---|
| Sprint | Sprint 2 - Modalidad aerea |
| Hito de salida | M2 - Flujo aereo validado |
| Estado | En curso |
| Avance | 0 de 7 tareas completadas |
| Inicio | 2026-07-13 |
| Fuente principal | `Tareas_Dokka_Scrapping.md` |
| Base funcional | PoC local `tools/poc_validacion.py` |
| Prerrequisito | Sprint 1 / M1 aprobado |
| Estimacion informada | 27 h, independiente de las estimaciones del backlog |

## Objetivo

Migrar, no reinventar, el flujo aereo que ya funciona en la PoC. Las funciones y reglas se copiaran y adaptaran a `app/scraper/aereo.py` y modulos auxiliares productivos, sin importar el archivo PoC durante la ejecucion.

## Tareas

| ID | Tarea | Estado |
|---|---|---|
| TICA-020 | Fixtures HTML aereos | En curso |
| TICA-021 | Momento 1: arribo y transportista | Pendiente |
| TICA-022 | Momento 2: movimiento ING | Pendiente |
| TICA-023 | Regla madre/hijo | Pendiente |
| TICA-024 | Momento 3: DUA | Pendiente |
| TICA-025 | Suite de tests aereos | Pendiente |
| TICA-026 | Validacion QA aerea / M2 | Pendiente |

## TICA-020 - Fixtures flujo aereo

**Estado:** En curso  
**Objetivo:** conservar HTML representativo y sanitizado para probar sin consultar TICA vivo.

Checklist:

- [x] Crear `tests/fixtures/aereo/` y definir reglas de sanitizacion.
- [x] Inventariar evidencia disponible del PoC.
- [ ] Obtener HTML del caso aereo `ok`.
- [ ] Obtener HTML del caso sin arribo.
- [ ] Obtener HTML del caso ambiguo madre/hijo.
- [ ] Sustituir identificadores y datos sensibles conservando la estructura HTML.
- [ ] Verificar que los fixtures no contengan datos reales innecesarios.

No habia archivos HTML crudos en el workspace al iniciar Sprint 2; solo reportes JSON/Markdown y capturas. No se fabricaran fixtures que pretendan ser reales: deben capturarse desde casos confirmados y luego sanitizarse.

## Decisiones heredadas y confirmadas

- La entrada sigue siendo `manifiesto` + `fecha_fin`; la modalidad se detecta desde Master.
- El PoC es la fuente funcional, pero no una dependencia del microservicio.
- `bultos` y `peso_bruto` son enteros; `3.000` en TICA representa `3000`.
- El consumidor decide por `estado`; el catalogo podra ampliarse mediante cambios futuros del contrato.
- Partidas arancelarias y valor/impuestos permanecen fuera del contrato vigente, aunque TICA-024 del archivo de tareas aun los mencione.
- Los tests no consultan TICA vivo.

## Registro de avances

| Fecha | Tarea | Avance | Estado |
|---|---|---|---|
| 2026-07-13 | Inicio Sprint 2 | M1 aprobado; se crea seguimiento e inventario de evidencia aerea. | En curso |
| 2026-07-13 | TICA-020 | Se confirma que no existen HTML crudos; se prepara la ruta y politica de fixtures sanitizados. | En curso |

## Evidencias

| Fecha | Verificacion | Resultado |
|---|---|---|
| 2026-07-13 | Inventario de `*.html` fuera de `.venv` | No existen fixtures TICA; solo `prueba html/index.html` ajeno al flujo |
| 2026-07-13 | Suite posterior al cierre M1 | 71 pruebas aprobadas; Ruff y mypy en verde |
