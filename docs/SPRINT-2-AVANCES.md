# Sprint 2 - Modalidad aerea - Seguimiento de avances

Documento vivo para migrar el flujo aereo validado en la PoC hacia codigo productivo.

## Estado general

| Dato | Estado |
|---|---|
| Sprint | Sprint 2 - Modalidad aerea |
| Hito de salida | M2 - Flujo aereo validado y aprobado |
| Estado | Completado |
| Avance | 7 de 7 tareas completadas |
| Inicio | 2026-07-13 |
| Cierre | 2026-07-15 |
| Fuente principal | `Tareas_Dokka_Scrapping.md` |
| Base funcional | PoC local `tools/poc_validacion.py` |
| Prerrequisito | Sprint 1 / M1 aprobado |
| Estimacion informada | 27 h, independiente de las estimaciones del backlog |

## Objetivo

Migrar, no reinventar, el flujo aereo que ya funciona en la PoC. Las funciones y reglas se copiaran y adaptaran a `app/scraper/aereo.py` y modulos auxiliares productivos, sin importar el archivo PoC durante la ejecucion.

## Tareas

| ID | Tarea | Estado |
|---|---|---|
| TICA-020 | Fixtures HTML aereos | Completada con excepcion documentada |
| TICA-021 | Momento 1: arribo y transportista | Completada |
| TICA-022 | Momento 2: movimiento ING | Completada |
| TICA-023 | Regla madre/hijo | Completada |
| TICA-024 | Momento 3: DUA | Completada |
| TICA-025 | Suite de tests aereos | Completada |
| TICA-026 | Validacion QA aerea / M2 | Completada |

## TICA-020 - Fixtures flujo aereo

**Estado:** Completada con excepcion documentada y aceptada

**Objetivo:** conservar HTML representativo y sanitizado para probar sin consultar TICA vivo.

No se dispuso de conocimientos reales sin fecha de arribo ni con varios movimientos
`ING`. No fue posible capturar HTML real de esas ramas. Los comportamientos `pending` y
`needs_review/ambiguedad_madre_hijo` quedaron cubiertos mediante fixtures estructurales y
pruebas offline. La limitacion fue declarada y aceptada para cerrar M2; si aparecen casos
reales en el futuro, deben capturarse y agregarse como regresion sin reabrir el desarrollo.

Checklist:

- [x] Crear `tests/fixtures/aereo/` y definir reglas de sanitizacion.
- [x] Inventariar evidencia disponible del PoC.
- [x] Obtener HTML real por pantalla del caso aereo `ok`.
- [x] Declarar que no se dispone de HTML real sin arribo y conservar fixture estructural.
- [x] Declarar que no se dispone de HTML real multi-ING y conservar fixture estructural.
- [x] Obtener HTML real de un caso con arribo pero sin movimiento Stock.
- [x] Sustituir identificadores y datos sensibles conservando la estructura HTML.
- [x] Verificar automaticamente que los fixtures reales no contengan los datos usados.

No habia archivos HTML crudos en el workspace al iniciar Sprint 2; solo reportes JSON/Markdown y capturas. No se fabricaran fixtures que pretendan ser reales: deben capturarse desde casos confirmados y luego sanitizarse.

`ok_hawb/` contiene las ocho pantallas reales del recorrido completo, sanitizadas en
memoria antes de escribirse. `sin_stock_mawb/` contiene las tres pantallas alcanzadas por
un MAWB con arribo que no expone movimiento `ING`. Los casos `sin_arribo.html` y
`madre_hijo_ambiguo.html` siguen siendo estructurales y estan rotulados como tales;
TICA-020 se cierra sin presentar los dos fixtures estructurales como evidencia real. El
flujo completo y el caso sin Stock si cuentan con HTML real sanitizado.

## TICA-026 - Validacion QA aerea

**Estado:** Completada - QA confirmado con la evidencia disponible

No se requieren otros identificadores solo para repetir las mismas comprobaciones. La
validacion puede reutilizar los casos reales ya ejecutados, siempre que QA contraste los
valores contra la consulta manual o evidencia del cliente y no se limite a aceptar la
salida automatica.

Avance disponible:

- Nueve identificadores aereos unicos ejecutados de forma independiente: cinco recorridos
  completos con Stock/DUA y cuatro MAWB con arribo sin Stock.
- Un flujo completo repetido para capturar las ocho pantallas HTML reales.
- Un MAWB repetido para capturar el recorrido real con arribo sin Stock.
- Suite offline completa con 95 pruebas aprobadas; Ruff y mypy en verde.
- Resultados detallados conservados fuera del repositorio en el reporte local de pruebas
  aereas.

Resultado de cierre:

- QA fue realizado con los casos aereos disponibles y su aprobacion fue confirmada en el
  seguimiento del proyecto el 2026-07-15.
- Se acepta como riesgo residual la ausencia de evidencia TICA viva para `sin_arribo` y
  multi-ING; no se confunde la cobertura estructural con una captura real.
- M2 queda aprobado y habilita el inicio del Sprint 3 maritimo.

Regla aclarada despues de QA: si no aparece ninguna fila para el conocimiento, el estado
es `not_found/manifiesto_no_encontrado`. Si la fila existe pero no contiene fecha de
arribo, el estado es `pending/arribo_pendiente` y el flujo se detiene sin consultar los
momentos posteriores. La regla tiene cobertura automatizada, aunque falta evidencia viva
del segundo escenario.

## Alcance tecnico implementado

- Momento 1 reutiliza la busqueda compartida y los datos confirmados de Master.
- Afectaciones conserva celdas y enlaces por fila; no usa el primer enlace global.
- Solo se consideran movimientos `ING`.
- La seleccion toma el unico movimiento `ING`, como el legacy validado. Si existen varios
  `ING`, no elige entre ellos sin una segunda regla confirmada.
- La ambiguedad devuelve `needs_review` con `ambiguedad_madre_hijo`.
- Detenciones aporta las dos fechas, bultos y peso; DUAs aporta numero y fecha.
- El codigo productivo no importa ni ejecuta `poc_validacion.py`.

## Diferencias corregidas respecto a la PoC

- La PoC seleccionaba el primer movimiento `ING`; produccion vincula cada movimiento con
  su propia fila. Conserva la prioridad legacy cuando existe un unico `ING`.
- Se restauran las esperas de tres segundos del legacy despues de cada navegacion porque
  GeneXus puede entregar `domcontentloaded` antes de completar las tablas.
- La fecha del DUA se obtiene abriendo su detalle, no desde la fecha de asociacion visible
  en la tabla.
- Los textos `Deposito`, `Depósito` y el mojibake heredado se toleran al extraer datos.
- Los parsers y la regla de seleccion tienen pruebas offline propias.

## Decisiones heredadas y confirmadas

- La API recibe `manifiestos` (1-100) + `fecha_fin` y una `fecha_inicio` opcional; cada manifiesto se procesa secuencialmente, detecta su modalidad desde Master y se publica como clave directa del JSON de respuesta.
- El PoC es la fuente funcional, pero no una dependencia del microservicio.
- `bultos` permanece entero; `peso_bruto` admite decimales y utiliza la normalización compartida del formato TICA. La validación
  con `PTY0036804` confirmo que `5.000` debe representar `5000`. La regla aplica
  tambien al flujo aereo.
- El consumidor decide por `estado`; el catalogo podra ampliarse mediante cambios futuros del contrato.
- Partidas arancelarias y valor/impuestos permanecen fuera del contrato vigente, aunque TICA-024 del archivo de tareas aun los mencione.
- Los tests no consultan TICA vivo.

## Registro de avances

| Fecha | Tarea | Avance | Estado |
|---|---|---|---|
| 2026-07-13 | Inicio Sprint 2 | M1 aprobado; se crea seguimiento e inventario de evidencia aerea. | En curso |
| 2026-07-13 | TICA-020 | Se confirma que no existen HTML crudos; se prepara la ruta y politica de fixtures sanitizados. | En curso |
| 2026-07-14 | Contrato transversal | Se incorpora consulta por lote secuencial sin modificar aun los parsers aereos. | Completada |
| 2026-07-14 | Response transversal | Se eliminan los envoltorios `regla` y `resultados`; cada manifiesto pasa a ser una clave directa del JSON. | Completada |
| 2026-07-14 | Fechas transversales | `fecha_inicio` pasa a ser opcional: omitida queda vacia en TICA; enviada se valida con maximo 15 dias inclusivos. | Completada |
| 2026-07-15 | TICA-021 a TICA-025 | Se migra el flujo aereo, se corrige seleccion ING/madre-hijo y se agregan pruebas offline. | Completadas |
| 2026-07-15 | TICA-020 | Se incorpora fixture `ok` derivado de evidencia PoC y dos fixtures estructurales rotulados. Faltan capturas reales equivalentes. | En curso |
| 2026-07-15 | TICA-020 | Se capturan y sanitizan ocho HTML reales de un HAWB completo y tres de un MAWB con arribo sin Stock. Se agregan pruebas offline de Stock, enlace por fila, Detenciones y ausencia de ING. | En curso |
| 2026-07-15 | TICA-020 | Se deja en amarillo: no existe entre los datos entregados un conocimiento real sin fecha de arribo. La rama permanece cubierta estructuralmente y pendiente de evidencia externa. | Amarillo |
| 2026-07-15 | TICA-026 | Se inicia QA reutilizando la matriz real ya ejecutada: 9 identificadores independientes, 5 completos y 4 con arribo sin Stock. Evidencia tecnica lista; falta contraste y aprobacion de QA. | Amarillo |
| 2026-07-15 | Cierre TICA-020 | Se acepta la falta de datos reales sin arribo y multi-ING; ambas ramas conservan cobertura estructural y quedan registradas como riesgo residual. | Completada con excepcion |
| 2026-07-15 | Cierre TICA-026 / M2 | QA confirmado con los casos disponibles; 7 de 7 tareas terminadas y Sprint 2 cerrado. | Completada |

## Evidencias

| Fecha | Verificacion | Resultado |
|---|---|---|
| 2026-07-13 | Inventario de `*.html` fuera de `.venv` | No existen fixtures TICA; solo `prueba html/index.html` ajeno al flujo |
| 2026-07-13 | Suite posterior al cierre M1 | 71 pruebas aprobadas; Ruff y mypy en verde |
| 2026-07-14 | Contrato por lote, response directo y fechas opcionales | 83 pruebas aprobadas; Ruff y mypy en verde |
| 2026-07-15 | Parsers, regla madre/hijo y regresion completa | 89 pruebas aprobadas; Ruff y mypy en verde |
| 2026-07-15 | Humo TICA caso `872219087246` | Clasificacion aerea y Momento 1 correctos; TICA no expuso enlaces posteriores en esta ejecucion y el servicio devolvio `pending/sin_dua`. M2 no se cierra con esta evidencia. |
| 2026-07-15 | Correccion prioritaria legacy y nueva prueba real `872219087246` | Se restauran esperas, columnas reales de Stock y detalle DUA. Resultado `ok` con movimiento `780677`, almacen `A283`, bultos/peso y DUA `005-2026-392058` de fecha `08/06/2026`. |
| 2026-07-15 | Captura HTML real TICA-020 | HAWB completo: 8 pantallas, estado `ok`; MAWB con arribo sin Stock: 3 pantallas, estado `sin_dua`. HTML crudo no se guarda y la auditoria automatica no encuentra identificadores reales ni tokens de navegacion. |
| 2026-07-15 | QA TICA-026 | 9 consultas reales independientes documentadas, fixtures reales parseables y regresion completa con 95 pruebas aprobadas; QA confirmado. |

El flujo aereo ya no responde `not_implemented`. M2 queda aprobado y Sprint 2 cerrado.

## Cierre M2 y riesgos residuales

- Codigo, pruebas, fixtures disponibles y documentacion son coherentes.
- QA fue confirmado con los casos reales disponibles.
- No existen datos reales para `sin_arribo` ni multi-ING. La limitacion se acepta para el
  cierre y debe convertirse en evidencia real cuando aparezcan casos adecuados.
- Suite final: 95 pruebas aprobadas, Ruff y mypy en verde.
