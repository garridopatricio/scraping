# Sprint 0 - Cierre PoC TICA

Documento vivo para ordenar el cierre del Sprint 0 (PoC de validacion) antes de pasar a la implementacion formal del scraper.

## Objetivo de la fase

Validar con casos reales si el portal publico de TICA permite obtener, sin credenciales ni CAPTCHA, los datos requeridos para cargas aereas y maritimas.

Esta fase no busca dejar codigo productivo. Busca responder:

- Que campos se pueden obtener publicamente.
- En que pantalla aparece cada dato.
- Que campos quedan pendientes y por que.
- Que reglas debe respetar el scraper productivo.
- Si el alcance futuro corresponde al mejor caso o al peor caso del backlog.

## Alcance declarado

Segun `BACKLOG-DESARROLLO.md`, Sprint 0 incluye:

- `TICA-001`: script PoC desechable con Playwright.
- `TICA-002`: ejecutar la PoC con casos reales y documentar hallazgos.
- Gate `M0`: definir si se puede avanzar a la implementacion formal.

## Casos usados

| Modalidad | Identificador | Fecha fin | Cedula | Estado |
|---|---:|---:|---:|---|
| Aereo | `05759349765` | `08/07/2026` | N/A | Ejecutado |
| Aereo | `872219087246` | `08/07/2026` | N/A | Ejecutado |
| Maritimo | `SMLU8904355A` | `09/07/2026` | `095144` | Ejecutado |
| Maritimo | `ENGB2600229` | `09/07/2026` | `095144` | Ejecutado |

## Resultado actual por modalidad

### Aereo

El flujo publico permite:

- Consultar conocimiento de embarque.
- Confirmar fecha de arribo.
- Entrar a lineas y afectaciones.
- Identificar movimiento de inventario en estado `ING`.
- Entrar a detenciones.
- Extraer movimiento, almacen fiscal, fechas, bultos y peso.
- Entrar a DUAs del movimiento cuando existe DUA.
- Extraer numero de DUA y fecha de registro del DUA.

Hallazgos:

- En el caso `05759349765`, no aparece DUA de nacionalizacion asociado al movimiento.
- En el caso `872219087246`, aparece DUA `005-2026-392058` con fecha `2026/06/08`.
- La razon social/transportista puede venir vacia; no se debe rellenar con codigos de descarga como `188AJU`.
- El campo `bultos` debe ser cantidad, no tipo de bulto.
- La pantalla `Lineas` puede usarse para navegar o detectar cantidad de lineas, pero no debe llenar campos finales si esos datos no estan confirmados por movimiento, Detenciones o DUA.
- La razon social/transportista se busca desde la columna/pantalla `Master` cuando existe, para evitar depender de valores vacios o codigos de la pantalla inicial.

Decision de alcance:

- `partidas_arancelarias` y `valor_aduanas_impuestos` ya no son campos necesarios ni requeridos para el alcance actual.
- Por esta razon se retiran del reporte `poc_resultado.md`, de la salida `poc_resultado.json` y del contrato funcional de la PoC.

### Maritimo

El flujo publico permite:

- Consultar BL en Conocimientos de Embarque.
- Confirmar fecha de arribo y transportista.
- Entrar a Lineas.
- Entrar a Afectaciones.
- Identificar DUA de movilizacion.
- Entrar al detalle del DUA de movilizacion.
- Guardar internamente el DUA de movilizacion como `aduana-anio-numero`.
- Extraer `Lugar de Destino` desde el detalle del DUA de movilizacion.
- Usar deposito destino, fecha y DUA de movilizacion para consultar Depositos -> Movimientos por Numero de Inventario.
- Filtrar el consolidado por cedula parcial.
- Entrar a Detenciones del movimiento encontrado.
- Extraer movimiento, fechas, bultos y peso desde Detenciones.
- Revisar DUAs del deposito.

Hallazgos:

- La cedula maritima `095144` fue entregada por el usuario y se usa como constante de la PoC para filtrar el consolidado. Esta decision podria cambiar en produccion si el negocio entrega otra cedula o exige cedula completa.
- La pantalla `Lineas` no debe llenar `almacen_fiscal`, `bultos` ni `peso_bruto` finales; esos datos solo quedan confirmados por Detenciones o por el DUA nacionalizacion consolidado segun corresponda.
- El DUA visible en Afectaciones es DUA de movilizacion, no nacionalizacion.
- El DUA de movilizacion debe quedar como dato interno y nunca debe devolverse como `dua_nacionalizacion`.
- Excepcion confirmada: si en el detalle del DUA el `Lugar de Destino` esta vacio o `-`, el pedido es anticipado; no se consulta Depositos y el DUA visible se reporta como `dua_nacionalizacion` junto con su fecha de registro.
- Para el caso `SMLU8904355A`, el DUA de movilizacion es `006-2026-007220`.
- Desde el detalle del DUA de movilizacion se obtiene `Lugar de Destino: A102- ALMACEN FISCAL Y DEPOSITO DE PAVAS S A`.
- Con cedula parcial `095144`, el flujo encuentra movimiento `1451`.
- En Detenciones del movimiento `1451` se obtiene:
  - fecha ingreso regimen: `19/01/26`
  - fecha movimiento inventario: `20/01/26 00:00`
  - bultos: `2.000`
  - peso bruto: `228.000`
- En DUAs del deposito para el movimiento `1451` no aparece DUA de nacionalizacion.
- En el caso `ENGB2600229` con cedula parcial `095144`, el flujo encuentra movimiento `55808682` en estado `ING`.
- Para `ENGB2600229`, en Detenciones se obtiene:
  - fecha ingreso regimen: `15/06/26`
  - fecha movimiento inventario: `15/06/26 00:00`
  - bultos: `422.000`
  - peso bruto: `5444.000`
- Para `ENGB2600229`, en DUAs del deposito aparece DUA de nacionalizacion `005-2026-414387` con fecha `2026/06/16`.
- Se valido que el DUA de movilizacion `002-2026-050020` no se devuelve como `dua_nacionalizacion`.
- Para casos con mas de una linea de mercancia, se navega usando la primera linea hasta llegar al DUA de nacionalizacion consolidado.
- En casos con mas de una linea, por ahora solo se reporta la informacion consolidada del DUA (`dua_nacionalizacion`, `fecha_dua`, `bultos`, `peso_bruto`). No se reportan datos operativos del movimiento/detenciones porque aun no esta definida la regla de negocio para decidir cual movimiento representa el consolidado.
- En `ENGB2600229`, el detalle del DUA `005-2026-414387` consolida las dos lineas y devuelve `Total Bultos: 614.000` y `Total Peso Bruto: 7450.000`.

Evidencia de consolidado con multiples coincidencias para cedula parcial:

![Consolidado maritimo con multiples coincidencias](../../evidencias/fase-0-maritimo-consolidado-multiples-coincidencias.png)

Evidencia de DUAs en otro movimiento del mismo consolidado:

![DUAs asociadas al movimiento 1458](../../evidencias/fase-0-maritimo-duas-movimiento-1458.png)

Observacion sobre seleccion de movimiento:

- La busqueda parcial por cedula puede devolver mas de una fila dentro del consolidado.
- En la evidencia, la cedula parcial `095144` aparece en movimientos distintos.
- Un movimiento puede estar en estado `FRA` y otro en estado `ING`.
- El movimiento `1458` muestra DUAs asociadas, mientras que `1451` no muestra DUA nacionalizacion.
- No queda confirmado que siempre deba tomarse el primer resultado.
- No queda confirmado que siempre deba tomarse solo `ING`; podria haber mas de un `ING` para la misma cedula parcial.
- Regla candidata para produccion: recopilar todas las coincidencias por cedula, priorizar/validar `ING`, y si hay mas de una candidata valida devolver `needs_review` o aplicar una segunda regla confirmada por Dökka.

## Filtros y reglas de decision

### Clasificacion aereo/maritimo

- La busqueda inicial siempre parte en `Conocimientos de Embarque`.
- Luego se abre `Master` para leer razon social/transportista y `Desc Descarga`.
- Si `Desc Descarga` contiene `Caldera`, `Moin` o `Puerto Limon` (sin distinguir mayusculas/tildes), el flujo se considera maritimo.
- Si `Desc Descarga` no contiene esos puertos, el flujo se considera aereo.
- Esta clasificacion es interna para decidir el camino; no es un campo de salida.

### Datos finales vs datos de navegacion

- `Lineas` puede indicar mas de una linea y puede entregar referencias utiles para navegar.
- `Lineas` no debe llenar `almacen_fiscal`, `bultos` ni `peso_bruto` como salida final.
- En aereo de una linea, los datos operativos salen desde movimiento/Detenciones y DUA si existe.
- En maritimo de una linea, los datos operativos salen desde Depositos/Detenciones y DUA si existe.
- En maritimo con varias lineas, el movimiento se usa solo como puente para llegar al DUA nacionalizacion consolidado; no se devuelven campos operativos del movimiento/detenciones hasta definir una regla de negocio.

### Pedido maritimo anticipado

- Si `Lugar de Destino` esta vacio o `-`, el pedido se considera anticipado.
- En ese caso no se consulta Depositos.
- El DUA visible en el detalle se usa como `dua_nacionalizacion`.
- La `Fecha de Registro` de ese DUA se usa como `fecha_dua`.
- Los campos de movimiento, almacen, fechas de movimiento, bultos y peso quedan pendientes salvo que una regla posterior indique otra fuente confiable.

### Maritimo con varias lineas

- Si hay mas de una linea, se sigue el flujo normal hasta Depositos cuando existe `Lugar de Destino`.
- Se usa la primera linea solo para navegar.
- Desde Depositos se entra al DUA asociado al movimiento encontrado.
- El DUA nacionalizacion se considera consolidado de las lineas.
- Solo se reportan desde ese DUA: `dua_nacionalizacion`, `fecha_dua`, `bultos` y `peso_bruto`.
- No se reportan por ahora: `movimiento_inventario`, `almacen_fiscal`, `fecha_ingreso_regimen`, `fecha_movimiento_inventario`.

### Depositos con multiples coincidencias por consignatario

- En el flujo maritimo normal, al llegar a Depositos se filtra por la cedula/consignatario entregada por el usuario.
- Puede existir mas de una fila para el mismo consignatario dentro del mismo resultado.
- Caso probado: `SMLU8904355A`, fecha fin `09/07/2026`, cedula parcial `095144`.
- El filtro devuelve 2 movimientos para consignatario `310109514431`:
  - Movimiento `1451`, estado `FRA`, fecha ingreso `19/01/26`, bultos `2.000`, tipo bulto `PAE`.
  - Movimiento `1458`, estado `ING`, fecha ingreso `19/01/26`, bultos `70.000`, tipo bulto `BOX`.
- Regla confirmada: despues de filtrar por consignatario, solo se debe tomar la fila con estado `ING`.
- Con esta regla, el caso `SMLU8904355A` debe seleccionar el movimiento `1458` y descartar el movimiento `1451` en estado `FRA`.

Riesgos que pasan a Fase 1/Fase 2:

- Definir regla productiva para multiples coincidencias por cedula dentro del consolidado.
- Definir si el filtro por cedula parcial es aceptable para produccion o si debe exigirse cedula completa.
- Definir que hacer si una misma cedula trae mas de un movimiento `ING`.
- Definir como reportar campos operativos de movimiento/detenciones cuando el conocimiento tiene mas de una linea.
- Definir si la existencia de DUA asociada debe ser criterio para seleccionar movimiento o solo dato posterior del movimiento ya seleccionado.

Preguntas abiertas para Dökka/Fase 1:

- La cedula `095144` queda fija para todos los maritimos o debe cambiar por cliente/importador?
- En produccion se permite seguir usando cedula parcial o se debe exigir cedula completa?
- Si hay mas de una coincidencia `ING` para la misma cedula, cual es la segunda regla de seleccion?
- Cuando hay varias lineas y un DUA consolidado, que debe mostrarse para `movimiento_inventario`, `almacen_fiscal`, `fecha_ingreso_regimen` y `fecha_movimiento_inventario`?
- Si hay varias lineas y mas de un DUA asociado, como se elige el DUA consolidado correcto?
- Para pedidos anticipados, se confirma que bultos/peso deben quedar pendientes si no hay fuente final distinta al DUA visible?

## Estado de los 10 campos requeridos

| Campo | Aereo | Maritimo | Resolucion actual |
|---|---|---|---|
| `fecha_arribo` | Publico | Publico | Se extrae desde Conocimientos de Embarque. |
| `transportista` | Publico si existe | Publico | Si viene vacio, queda pendiente/no disponible. |
| `movimiento_inventario` | Publico | Publico tras Depositos | En maritimo requiere DUA movilizacion + deposito + cedula. |
| `almacen_fiscal` | Publico | Publico si aplica | Debe venir de movimiento/destino confirmado; no desde `Lineas`. En varias lineas queda pendiente hasta definir regla. |
| `fecha_ingreso_regimen` | Publico | Publico tras Detenciones | Se extrae desde Detenciones. |
| `fecha_movimiento_inventario` | Publico | Publico tras Detenciones | Se extrae desde Detenciones. En varias lineas queda pendiente hasta definir regla. |
| `bultos` | Publico | Publico | Debe ser cantidad, no tipo de bulto. En varias lineas sale del DUA consolidado. |
| `peso_bruto` | Publico | Publico | No se reporta desde `Lineas`. En varias lineas sale del DUA consolidado. |
| `dua_nacionalizacion` | Publico si existe | Publico si existe | No confundir con DUA de movilizacion. Validado en maritimo con `ENGB2600229`. |
| `fecha_dua` | Publico si existe | Publico si existe | Requiere DUA de nacionalizacion confirmado. Validado en maritimo con `ENGB2600229`. |

Campos retirados del alcance:

| Campo retirado | Decision | Motivo |
|---|---|---|
| `partidas_arancelarias` | No requerido | Se establecio que no sera necesario para el alcance actual. |
| `valor_aduanas_impuestos` | No requerido | Se establecio que no sera necesario para el alcance actual. |

## Reglas confirmadas para produccion

- No inventar datos: si no aparece, marcar `pending`, `unavailable` o `not_found` segun corresponda.
- Si no hay fecha de arribo, detener el flujo.
- Aereo:
  - El movimiento sale desde Lineas/Afectaciones.
  - Debe filtrarse estado `ING`.
  - El `ING` de aereo aplica sobre Movimientos de Stock.
  - `Lineas` no llena datos finales; los campos finales se toman del movimiento/Detenciones/DUA segun corresponda.
  - Si hay mas de una linea y existe DUA nacionalizacion, se reportan solo `fecha_dua`, `dua_nacionalizacion`, `bultos` y `peso_bruto` desde el detalle consolidado del DUA. Los campos operativos de movimiento quedan pendientes hasta definir regla de negocio.
  - La ambiguedad madre/hijo debe resolverse con regla o `needs_review` en Fase 2.
- Maritimo:
  - El DUA de Afectaciones es DUA de movilizacion.
  - El DUA de movilizacion nunca debe devolverse como nacionalizacion.
  - Excepcion: si `Lugar de Destino` esta vacio o `-`, se considera pedido anticipado; no se consulta Depositos y el DUA visible se usa como nacionalizacion.
  - El deposito debe salir del detalle del DUA de movilizacion, campo `Lugar de Destino`.
  - `Lineas` no llena datos finales; solo sirve para navegar y detectar cantidad de lineas.
  - En una sola linea, bultos y peso deben salir de Detenciones del movimiento filtrado por cedula.
  - Si hay mas de una linea y existe DUA nacionalizacion, se reportan solo `fecha_dua`, `dua_nacionalizacion`, `bultos` y `peso_bruto` desde el detalle consolidado del DUA. Los campos operativos de movimiento quedan pendientes hasta definir regla de negocio.
  - Si no se encuentra la cedula, no devolver movimiento de otra empresa.
  - Si hay mas de una coincidencia por cedula, no asumir automaticamente que la primera fila es la correcta.

## Estado para cerrar Sprint 0

Sprint 0 queda listo para cierre del Gate M0.

Validaciones completas:

1. Los 10 campos requeridos quedaron definidos en el contrato actual de la PoC.
2. `partidas_arancelarias` y `valor_aduanas_impuestos` fueron retirados del alcance.
3. Se valido flujo aereo con DUA nacionalizacion visible.
4. Se valido flujo maritimo con DUA nacionalizacion visible.
5. Se documento el riesgo de multiples coincidencias por cedula para resolverlo como regla productiva posterior.
6. `poc_resultado.md` y `poc_resultado.json` fueron actualizados como evidencia final.

## Declaracion propuesta de cierre

Sprint 0 puede cerrarse cuando podamos afirmar:

> Se valido que el portal publico de TICA permite obtener los datos requeridos para cargas aereas y maritimas sin login ni CAPTCHA, incluyendo DUA de nacionalizacion cuando existe y es visible. El flujo maritimo requiere tratar el DUA de movilizacion como dato interno y buscar el movimiento real por Depositos. Los campos de partidas arancelarias y valor/impuestos fueron retirados del alcance porque se establecio que no seran necesarios ni requeridos. Con esta evidencia, Gate M0 queda cerrado favorablemente para avanzar a Fase 1.

## Proyeccion posterior al gate

Si Sprint 0 se cierra favorablemente, el siguiente paso es Sprint 1:

- Crear estructura productiva del servicio.
- Definir modelos de entrada/salida.
- Implementar browser manager con reintentos.
- Implementar orquestador con estados.
- Agregar cache y logging.
- Exponer API FastAPI.

Luego:

- Fase 2 migra el flujo aereo a `app/scraper/aereo.py` con fixtures y tests.
- Fase 3 migra el flujo maritimo a `app/scraper/maritimo.py` con fixtures y tests.
- Fase 4 integra RAGA Orders contra la API.

## Registro de decisiones

| Fecha | Decision | Motivo |
|---|---|---|
| 2026-07-09 | `bultos` representa cantidad, no tipo de bulto. | Paso a paso pide cantidad de bultos. |
| 2026-07-15 | En el contrato productivo, `bultos` y `peso_bruto` son enteros; TICA presenta tres decimales. | Correccion QA M3: `3.000` debe publicarse como `3`. |
| 2026-07-09 | En maritimo, bultos/peso se reportan desde Detenciones. | Deben corresponder al movimiento filtrado por cedula. |
| 2026-07-09 | DUA de movilizacion se guarda interno y no se reporta como nacionalizacion. | Regla dura del backlog y paso a paso. |
| 2026-07-09 | `Lugar de Destino` del DUA de movilizacion define el deposito para consultar Depositos. | Paso a paso especifica deposito destino desde DUA de movilizacion. |
| 2026-07-09 | Transportista vacio no debe reemplazarse con codigo de descarga. | Evita datos falsos por columnas vacias en TICA. |
| 2026-07-12 | `partidas_arancelarias` y `valor_aduanas_impuestos` se retiran del alcance. | Se establecio que no seran necesarios ni requeridos para el alcance actual. |
| 2026-07-12 | Gate M0 queda cerrable y se puede avanzar a Fase 1. | Se valido aereo y maritimo con los 10 campos requeridos, incluyendo DUA nacionalizacion cuando existe y es visible. |
| 2026-07-12 | Si `Lugar de Destino` esta vacio o `-`, el maritimo es anticipado. | En este caso no se consulta Depositos y el DUA visible se reporta como nacionalizacion. |
| 2026-07-12 | En casos con varias lineas, se reporta solo informacion consolidada del DUA nacionalizacion. | Aun no esta definida la regla para elegir que movimiento/detencion representa el consolidado; validado con `ENGB2600229`. |
| 2026-07-13 | La cedula maritima `095144` queda como constante de la PoC. | Fue entregada por el usuario; podria cambiar a futuro segun regla de negocio. |
| 2026-07-13 | `Lineas` no debe llenar campos finales. | Solo se usa para navegar/detectar cantidad de lineas; evita reportar datos preliminares como finales. |
| 2026-07-13 | La clasificacion aereo/maritimo se decide por `Desc Descarga` en `Master`. | `Caldera`, `Moin` o `Puerto Limon` indican maritimo; otros valores se tratan como aereo. |
| 2026-07-13 | En Depositos maritimos, luego de filtrar por consignatario, solo se selecciona estado `ING`. | Validado con `SMLU8904355A`: descarta movimiento `1451` `FRA` y selecciona `1458` `ING`. |
