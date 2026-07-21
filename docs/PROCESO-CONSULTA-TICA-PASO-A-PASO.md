  
RAGA Orders – Grupo Dökka

**Proceso de Consulta en el Sistema TICA**

*Documentación técnica – Paso a Paso por Modalidad de Carga*

| Elaborado a partir de: | Sesión técnica del 10 de marzo de 2026 |
| :---- | :---- |
| **Fuente:** | Nataly Castillo Muñoz – Grupo Dökka |
| **Fecha del documento:** | Junio 2026 |
| **Proyecto:** | RAGA Orders – Central Farmacéutica, S.A. |

# **1\. Contexto y Propósito**

Este documento formaliza el proceso de consulta en el sistema TICA (Tecnología de Información para el Control Aduanero del Ministerio de Hacienda de Costa Rica), tal como fue demostrado en vivo por Nataly Castillo Muñoz de Grupo Dökka durante la sesión técnica del 10 de marzo de 2026\.

El objetivo de la sesión fue brindar a Raga-x el conocimiento operativo del proceso manual actual, a fin de definir la propuesta técnica de automatización mediante la integración con dicho portal.

| *⚠️  TICA es una plataforma gubernamental del Ministerio de Hacienda. No ofrece API pública ni notificaciones automáticas. La automatización propuesta se basa en web scraping directo del portal.* |
| :---- |

## **1.1 Rol de TICA en el proceso de importación**

TICA es la fuente de verdad oficial para toda la información en firme de la carga importada. A diferencia de los sistemas de tracking de aerolíneas o agentes de carga, los datos registrados en TICA representan hechos confirmados, no estimaciones.

* Tracking de transportistas (DHL, aerolíneas, etc.): información estimada y de seguimiento en tránsito.

* TICA: información oficial y en firme; única fuente válida para iniciar trámites de nacionalización.

Una vez que la carga aparece registrada en TICA, todas las consultas posteriores del proceso se realizan exclusivamente en este sistema.

## **1.2 Los 3 Momentos Operativos Clave**

El equipo de Grupo Dökka identifica tres momentos críticos en los que se debe consultar el sistema TICA:

| \# | Momento | Qué se verifica | Impacto si no existe |
| ----- | ----- | ----- | ----- |
| 1 | Arribo | Verificar si la carga ya tiene fecha de arribo registrada en TICA. | Sin fecha de arribo no existen eventos posteriores; el proceso no puede continuar. |
| 2 | Movimiento de Inventario | Aparece 1-2 días después del arribo. Es el ingreso de la carga al almacén fiscal. | Sin este dato la agencia aduanal no puede iniciar el trámite de nacionalización. |
| 3 | Generación del DUA | El DUA (Documento Único Aduanero) de nacionalización ya ha sido emitido. | Es cuando se obtiene la mayor parte de datos: bultos, peso, partidas arancelarias, almacén fiscal, etc. |

# **2\. Proceso de Consulta – Carga Aérea**

La carga aérea es la modalidad más directa de consultar en TICA. El dato de entrada es la guía aérea (también llamada conocimiento de embarque aéreo).

## **2.1 Datos de entrada requeridos**

* Número de guía aérea (conocimiento de embarque)

* Fecha fin aproximada de arribo (para filtrar la búsqueda)

## **2.2 Paso a Paso – Momento 1: Verificación de Arribo**

| Paso | Acción | Detalle |
| :---: | ----- | ----- |
| **1** | **Ingresar a TICA** | Acceder al portal del Ministerio de Hacienda (TICA). |
| **2** | **Ir a Manifiestos** | Navegar a la sección: Manifiestos → Conocimientos de Embarque. |
| **3** | **Ingresar datos de búsqueda** | Colocar la Fecha Fin (30 días \+ de la fecha actual)  y el Número de Conocimiento de Embarque (guía aérea / BL). |
| **4** | **Verificar fecha de arribo** | El sistema devuelve la fecha oficial de arribo de la carga. Este es el primer dato clave. |
| **5** | **Decisión** | Si existe fecha de arribo → continuar al Momento 2\. Si no existe → la carga aún no ha sido registrada en TICA; reintentar más tarde. |

| *📌  Nota: Si existe discrepancia entre la fecha del tracking del transportista y la fecha en TICA, la fecha de TICA es siempre la que prevalece. Puede ocurrir que la carga haya tenido un roleo y la fecha real sea diferente a la estimada originalmente.* |
| :---- |

## 

## **2.3 Paso a Paso – Momento 2: Movimiento de Inventario**

| Paso | Acción | Detalle |
| :---: | ----- | ----- |
| **1** | **Ir a Líneas y Afectaciones** | Desde el resultado del conocimiento de embarque, acceder a la sección de Líneas y Afectaciones. |
| **2** | **Localizar el Movimiento de Inventario** | Para carga aérea, aquí aparecerá directamente un número de movimiento de inventario (no un DUA de traslado como en marítimo). |
| **3** | **Filtrar por estado ING** | Es crítico seleccionar únicamente movimientos en estado 'ING' (ingreso). Puede existir un movimiento 'madre' (palet completo) y uno 'hijo' (bultos contados). El correcto para la nacionalización es el movimiento hijo en estado ING. |
| **4** | **Registrar datos del movimiento** | Anotar: número de movimiento de inventario, nombre del almacén fiscal (depósito), fecha de ingreso al régimen, fecha del movimiento de inventario, cantidad de bultos, peso, transportista. |

| *⚠️  Diferencia importante: La fecha de ingreso al régimen y la fecha del movimiento de inventario son datos distintos. Pueden coincidir (si el almacén registró rápido) o diferir en varios días. Ambas fechas deben capturarse.* |
| :---- |

## **2.4 Paso a Paso – Momento 3: Consulta del DUA**

| Paso | Acción | Detalle |
| :---: | ----- | ----- |
| **1** | **Ir a la sección de DUAs** | Desde el registro del movimiento de inventario, navegar a la sección de DUAs. |
| **2** | **Verificar si existe DUA generado** | Si ya existe DUA: continuar. Si no: la agencia aduanal aún no ha completado el trámite ante la aduana; reintentar más tarde. |
| **3** | **Obtener datos del DUA** | Registrar: número de DUA, aduana, año, quién tramitó, peso, bultos, valor de aduanas, partidas arancelarias, fecha de generación del DUA. |
| **4** | **Alimentar el reporte** | Todos estos datos son los que actualmente el equipo traslada manualmente al reporte de tránsito en Excel. |
| **5** | **Decisión** | Si existe DUA → continuar al Momento 2.5 Si no existe → la carga aún no ha sido registrada en TICA; reintentar más tarde. |

## **2.5 Datos que se obtienen en el proceso aéreo completo**

| Sección TICA | Dato obtenido | Momento |
| ----- | ----- | ----- |
| Manifiestos / Conocimientos de embarque | Fecha de arribo | Momento 1 |
| Manifiestos / Conocimientos de embarque | Razón social del transportista | Momento 1 |
| Líneas y Afectaciones | Número de movimiento de inventario | Momento 2 |
| Líneas y Afectaciones | Nombre del almacén fiscal (depósito) | Momento 2 |
| Líneas y Afectaciones | Fecha de ingreso al régimen | Momento 2 |
| Líneas y Afectaciones | Fecha del movimiento de inventario | Momento 2 |
| Líneas y Afectaciones | Cantidad de bultos | Momento 2 |
| Líneas y Afectaciones | Peso bruto | Momento 2 |
| DUAs | Número de DUA de nacionalización | Momento 3 |
| DUAs | Fecha del DUA | Momento 3 |
| DUAs | Partidas arancelarias | Momento 3 |
| DUAs | Valor de aduanas / impuestos | Momento 3 |

# **3\. Proceso de Consulta – Carga Marítima**

La carga marítima sigue una ruta de consulta más compleja que la aérea, porque el DUA visible en la primera pantalla no es el DUA de nacionalización, sino el de movilización de carga (traslado de puerto a almacén fiscal). Es necesario un paso intermedio adicional.

## **3.1 Datos de entrada requeridos**

* Número de Bill of Lading (BL / MBL)

* Número de cédula jurídica de la empresa importadora

* Fecha fin aproximada de arribo

## **3.2 Paso a Paso Completo**

| Paso | Acción | Detalle |
| :---: | ----- | ----- |
| **1** | **Ingresar a TICA → Manifiestos** | Navegar a: Manifiestos → Conocimientos de Embarque. |
| **2** | **Ingresar BL y fecha fin** | Colocar el número de BL y la fecha fin de búsqueda. Se obtiene: fecha de arribo, empresa transportista. |
| **3** | **Ir a Líneas y Afectaciones** | En este punto, para cargas marítimas, NO aparece un movimiento de inventario directo. En su lugar aparece un DUA de movilización de carga (traslado de puerto a almacén fiscal). |
| **4** | **Identificar el DUA de movilización** | ⚠️ Este DUA NO es el DUA de nacionalización. Es el DUA de traslado. Anotar: número de DUA de movilización, aduana (ej. 006), año, número de depósito destino (ej. A-102) y fecha. |
| **5** | **Ir a Depósitos → Movimientos por Número de Inventario** | Navegar a la sección: Depósitos → Movimientos por Número de Inventario. NO ir a DUAs directamente en este paso. |
| **6** | **Ingresar datos del depósito** | Colocar: número de depósito (obtenido en paso 4), fecha (aproximada al mes del DUA de movilización) y el número de DUA de movilización (aduana \+ año \+ número). |
| **7** | **Filtrar por cédula jurídica propia** | El sistema devuelve todas las cargas del consolidado. Filtrar por el número de cédula jurídica de la empresa para encontrar el movimiento que corresponde. |
| **8** | **Identificar el movimiento de inventario correcto** | En la sección de Detenciones aparece el movimiento de inventario real del ingreso al almacén fiscal. Anotar: número de movimiento, depósito, fecha de ingreso al régimen, fecha del movimiento de inventario, bultos y peso. |
| **9** | **Verificar DUA en sección Duas del depósito** | Desde el mismo módulo de depósitos, verificar si ya existe DUA generado para esa carga. Si existe: registrar los datos del DUA de nacionalización. |

Reglas productivas confirmadas:

- La cedula usada por el servicio es `095144`, configurable con
  `TICA_CEDULA_JURIDICA_MARITIMA`; no se envia en el request.
- Cada linea se recorre por separado conservando los enlaces de su propia fila. Con
  varias lineas se publican todos los registros en `momento2.movimientos` y un solo DUA
  consolidado de nacionalizacion.
- Si `Lugar de Destino` esta vacio, el pedido es anticipado: se conserva el DUA inicial
  y su fecha como Momento 3, Momento 2 queda vacio y no se navega a Depositos.
- Si no aparece la cedula configurada se responde `not_found/cedula_no_encontrada`. Si
  falta arribo o DUA final se responde `pending`, conservando los momentos ya obtenidos.

| *⚠️  Diferencia crítica con Aéreo: En marítimo, el DUA visible en la primera pantalla (Líneas y Afectaciones) es el DUA de MOVILIZACIÓN (traslado del puerto al almacén fiscal), no el de nacionalización. El DUA de nacionalización se encuentra en la sección de Depósitos, después de seguir el proceso completo descrito.* |
| :---- |

| *📌  Ejemplo real documentado en sesión: DUA de movilización aduana 006, año 2026, número 007220 → Depósito A-102 → Movimiento de inventario \#1451 → Ingreso al régimen 19 enero 2026, movimiento digitado 20 enero 2026, 2 bultos, 228 kg.* |
| :---- |

# **4\. Proceso de Consulta – Carga Terrestre**

La carga terrestre comienza por Número DUA y requiere que el usuario resuelva manualmente el CAPTCHA mostrado por TICA.

## **4.1 Diferencia fundamental**

| *La entrada confirmada es el Número DUA. Dokka acepta guiones o espacios, elimina comillas y separa aduana, año y correlativo antes de consultar TICA.* |
| :---- |

## **4.2 Datos de entrada requeridos**

* Número DUA en tres grupos numéricos, por ejemplo `005-2026-470211`.

* CAPTCHA introducido manualmente por el usuario en el modal de SD Editar.

* Después del detalle inicial se navega a Manifiesto/Stock, movimiento y Detenciones.

# **5\. Comparación por Modalidad de Carga**

| Aspecto | Aérea | Marítima | Terrestre |
| ----- | ----- | ----- | ----- |
| Identificador de búsqueda | Guía aérea | Número de BL/MBL | Número DUA |
| Sección inicial en TICA | Manifiestos → Conocimientos de embarque | Manifiestos → Conocimientos de embarque | Consulta DUA → CAPTCHA |
| ¿Aparece Mov. Inventario directamente? | Sí – en Líneas y Afectaciones | No – aparece DUA de movilización primero | Se obtiene desde Manifiesto/Stock |
| Pasos intermedios adicionales | Ninguno | Ir a Depósitos → Mov. por Nro. Inventario | Resolver CAPTCHA → Manifiesto/Stock → Movimiento → Detenciones |
| Complejidad relativa | Baja | Media-Alta | Alta por sesión humana y navegación posterior |

# **6\. Consideraciones Técnicas para la Automatización**

## **6.1 Inestabilidad del portal TICA**

Durante la misma sesión de demostración (10 de marzo), el portal TICA no cargó por varios minutos. Nataly señaló que esto no es frecuente pero ocurre, especialmente cuando el Ministerio realiza actualizaciones.

| *⚠️  Implicación para el diseño: La solución de web scraping debe contemplar reintentos automáticos y manejo de errores cuando el portal no esté disponible, sin que eso interrumpa el flujo general de RAGA Orders.* |
| :---- |

## **6.2 Limitaciones del scraping vs. integración directa**

Se exploró la posibilidad de integración directa con TICA o mediante intermediarios. La conclusión fue:

* No existe API pública de TICA.

* Ningún intermediario en el mercado tiene conexión activa establecida con TICA al momento de la sesión.

* La opción más viable es el web scraping directo del portal.

* Riesgo: cualquier cambio en la estructura de la página web de TICA puede detener el proceso de consulta automatizado.

## **6.3 Cobertura de almacenes fiscales**

Una alternativa explorada fue recibir información de TICAL (agencia aduanal) directamente por correo o Excel. Sin embargo, esta opción fue descartada porque:

* TICAL solo cubre las cargas que maneja directamente.

* Grupo Dökka trabaja con múltiples almacenes fiscales: Terminales Santa María, Terminales Unidas, Almacén Fiscal Cariari, entre otros.

* La automatización debe funcionar independientemente del almacén fiscal, lo que refuerza que TICA es la fuente correcta al centralizarlos a todos.

## **6.4 Campos requeridos en RAGA Orders**

A partir de este análisis, se identificaron los siguientes campos que RAGA Orders debe contemplar en el módulo de embarques para soportar la integración:

| Campo | Aplica a | Fuente |
| ----- | ----- | ----- |
| Número de conocimiento de embarque (múltiples por shipment) | Aéreo y Marítimo | Proveedor / Freight Forwarder |
| Número DUA | Terrestre | Shipping Document / TICA |
| Fecha de arribo (TICA) | Todas | Extraído de TICA |
| Número de movimiento de inventario | Todas | Extraído de TICA |
| Almacén fiscal (depósito) | Todas | Extraído de TICA |
| Fecha de ingreso al régimen | Todas | Extraído de TICA |
| Fecha del movimiento de inventario | Todas | Extraído de TICA |
| Cantidad de bultos | Todas | Extraído de TICA |
| Peso bruto | Todas | Extraído de TICA |
| Número de DUA de nacionalización | Todas | Extraído de TICA |
| Fecha del DUA | Todas | Extraído de TICA |
| Partidas arancelarias | Todas | Extraído de TICA |

# **7\. Pendientes Identificados en la Sesión**

| Pendiente | Responsable | Estado |
| ----- | ----- | ----- |
| Recorrido terrestre y ejemplos reales | Grupo Dökka | Confirmado e implementado |
| Identificador de búsqueda terrestre | Grupo Dökka | Confirmado: Número DUA |
| Propuesta técnica final de integración por web scraping | Juan Castillo – Raga-x | Comprometido para la semana siguiente a la sesión |
| Asignación de recurso IT cliente para validaciones (sustituto de Jerson Morales) | Nataly Castillo \+ Jefatura Grupo Dökka | En gestión interna |

*— Documento elaborado por Raga-x a partir de la sesión técnica del 10 de marzo de 2026 —*
# Implementacion productiva del flujo aereo (Sprint 2 completado)

El Sprint 2 y el hito M2 fueron cerrados el 2026-07-15 con QA confirmado. No se
dispusieron casos reales sin fecha de arribo ni con varios movimientos `ING`; esas ramas
quedan cubiertas mediante fixtures estructurales y registradas como riesgo residual hasta
que aparezcan datos reales adecuados.

El servicio busca el conocimiento una sola vez, abre Master y usa `Desc Descarga` para
clasificar la modalidad. Para aereo ejecuta el siguiente recorrido:

1. **Momento 1:** toma fecha de arribo del conocimiento y transportista de Master. Si el
   conocimiento existe pero no tiene fecha de arribo, devuelve
   `pending/arribo_pendiente` y termina la consulta de ese elemento: no pregunta Lineas,
   Stock, Detenciones ni DUA.
2. **Lineas y Afectaciones:** navega por los enlaces del conocimiento y lee las filas de
   Afectaciones conservando sus enlaces. Solo considera filas en estado `ING`.
3. **Madre/hijo:** toma el unico movimiento de Stock en estado `ING`, siguiendo el legacy
   validado. La fila de Afectaciones no contiene el conocimiento como columna; la relacion
   se observa en el detalle de Stock. Si aparecen varios `ING` y no existe una segunda
   regla confirmada, devuelve `needs_review` con `ambiguedad_madre_hijo`.
4. **Momento 2:** desde el movimiento elegido y Detenciones obtiene movimiento, almacen,
   fecha de ingreso al regimen, fecha del movimiento, bultos y peso bruto.
5. **Momento 3:** abre los DUAs asociados al movimiento y luego el detalle del DUA. El
   numero sale de la tabla y la fecha de registro del detalle; la fecha de asociacion no se
   publica como `fecha_dua`. Si no existe DUA, conserva lo anterior y devuelve `pending`.

Estados relevantes: `not_found/manifiesto_no_encontrado` si la busqueda inicial no
encuentra el conocimiento; `pending/arribo_pendiente` si lo encuentra pero no tiene fecha
de arribo; `pending` si falta el DUA; `needs_review` si madre/hijo es ambiguo, `unavailable`
ante fallo del portal sin cache, `stale` con cache utilizable y `ok` con DUA confirmado.

Las pruebas automatizadas usan HTML sanitizado y nunca consultan TICA vivo.

El contrato vigente publica 10 campos. Partidas arancelarias y valor/impuestos quedan
fuera del alcance actual aunque aparezcan en secciones historicas de este documento.
