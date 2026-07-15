# Sprint 3 - Modalidad maritima - Seguimiento de avances

Documento vivo para migrar el flujo maritimo validado en la PoC hacia codigo productivo.

## Estado general

| Dato | Estado |
|---|---|
| Sprint | Sprint 3 - Modalidad maritima |
| Hito de salida | M3 - Flujo maritimo validado |
| Estado | Completado; M3 aprobado |
| Avance | 7 de 7 tareas completadas |
| Inicio | 2026-07-15 |
| Fuente funcional | `tools/poc_validacion.py` y comparaciones reales legacy-servicio |
| Tarea activa | Ninguna; siguiente fase Sprint 4 |

## Alcance implementado

- Cedula maritima predeterminada `095144`, centralizada en configuracion y reemplazable
  con `TICA_CEDULA_JURIDICA_MARITIMA`; no forma parte del request publico.
- Separacion interna entre DUA de movilizacion y DUA de nacionalizacion.
- Recorrido por cada fila de Lineas/Afectaciones, conservando el enlace propio.
- Busqueda en Depositos por deposito, ventana de fecha y DUA de movilizacion; filtro
  estricto por cedula y estado `ING`.
- Pedido anticipado: publica el DUA inicial, no visita Depositos y deja Momento 2 vacio.
- Multilinea: devuelve todos los movimientos en `momento2.movimientos` y un solo DUA
  consolidado. Los escalares solo se completan cuando existe un movimiento.
- Sin DUA final devuelve `pending`, conservando movimientos; cedula ausente devuelve
  `not_found/cedula_no_encontrada`.
- Aereo conserva su comportamiento y devuelve `movimientos: []`.

## Estado por tarea

| ID | Estado | Evidencia |
|---|---|---|
| TICA-030 | Completada | Tres capturas reales sanitizadas: normal, anticipado y consolidado multilinea. |
| TICA-031 | Completada | Arribo, transportista, Lineas/Afectaciones y DUA de movilizacion migrados. |
| TICA-032 | Completada | Navegacion a Depositos por cada linea y Detenciones. |
| TICA-033 | Completada | Filtro configurable `095144` + `ING`; nunca usa otra empresa. |
| TICA-034 | Completada | DUA final consolidado y excepcion anticipada separadas. |
| TICA-035 | Completada | Suite offline, regresion, Ruff y mypy en verde. |
| TICA-036 | Completada | Tres respuestas publicas comparadas; M3 aprobado. |

## HTML reales y sanitizacion

Los fixtures se encuentran en `tests/fixtures/maritimo/`, separados por caso y pantalla:

| Caso | Pantallas | Resultado observado |
|---|---:|---|
| `normal_una_linea` | 9 | Un movimiento, escalares compatibles y DUA final. |
| `anticipado` | 5 | DUA inicial publicado; no existen pantallas de Depositos. |
| `consolidado_multilinea` | 13 utiles | Dos lineas, dos movimientos/Detenciones y un DUA final. |

Solo se guarda HTML sanitizado. Se reemplazan BL, manifiestos, cedulas, DUAs, numeros de
movimiento, nombres, razones sociales, correos, estados ocultos GeneXus y parametros de
enlaces. Se preservan DOM, filas, columnas, estado `ING`, fechas y magnitudes necesarias
para probar los parsers. `tests/test_maritimo.py` rechaza los identificadores reales usados.

## Comparacion legacy - servicio

### Flujo normal de una linea

Ambas ejecuciones devolvieron exactamente los mismos datos funcionales: arribo
`05/05/26`, movimiento `55791518`, ingreso/movimiento `13/05/26`, 386 bultos, peso 4558,
DUA final `005-2026-360544` y fecha `2026/05/26`. Los identificadores se anotan aqui como
evidencia operativa autorizada, pero no aparecen en fixtures.

### Pedido anticipado

Legacy y servicio coincidieron en arribo `28/06/26`, Momento 2 vacio, DUA inicial
`002-2026-055881` y fecha `2026/06/27`. Produccion se detuvo antes de Depositos.

### Consolidado multilinea

La primera integracion eligio el primer enlace global y obtuvo solo 422 bultos/5444 de
peso. El HTML mostro dos filas. Se corrigio la asociacion fila-enlace y el servicio obtuvo
dos movimientos: 422 + 192 bultos y 5444 + 2006 de peso, iguales a los totales legacy
614/7450, con un unico DUA final `005-2026-414387`.

Una ejecucion inicial con fecha fin `31/01/2026` devolvio `not_found` tanto en legacy como
en servicio; no era una diferencia de parser, sino una ventana de consulta incorrecta.

## Pruebas y cierre

- Suite automatizada completamente offline; ningun test consulta TICA vivo.
- Casos cubiertos: normal, anticipado, multilinea, filtro cedula/ING, cedula ausente,
  arribo pendiente, DUA pendiente, contrato tipado y regresion aerea/lote/cache/estados.
- TICA-036 repitio mediante la ruta publica los tres casos autorizados. Normal y
  anticipado coinciden campo por campo con legacy; multilinea devuelve los dos
  movimientos y un unico DUA consolidado.
- Durante QA se corrigio la interpretacion de cantidades: `386.000` representa `386`, no
  `386000`. La segunda ejecucion publica confirmo 386/4558 y, para multilínea,
  422/5444 + 192/2006 = 614/7450.
- Partidas arancelarias y valor/impuestos permanecen fuera del contrato.

## Registro diario

| Fecha | Tarea | Avance | Estado |
|---|---|---|---|
| 2026-07-15 | TICA-030 | Capturas reales sanitizadas normal, anticipada y multilinea. | Completada |
| 2026-07-15 | TICA-031-034 | Flujo productivo, cédula fija configurable, anticipado y multilinea. | Completadas |
| 2026-07-15 | Diagnostico | Corregido selector global que omitia la segunda linea. | Resuelto |
| 2026-07-15 | TICA-035 | Parsers, fixtures, contrato y regresion automatizada. | Completada |
| 2026-07-15 | QA cantidades | Corregida la lectura de tres decimales y repetida la suite completa. | Resuelto |
| 2026-07-15 | TICA-036 / M3 | Tres casos reales validados mediante respuesta publica; Sprint 3 cerrado. | Completada |
