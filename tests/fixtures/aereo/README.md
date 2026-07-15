# Fixtures aereos

Esta carpeta contiene HTML sanitizado derivado de casos reales confirmados en TICA y
fixtures estructurales para los casos limite que todavia no tienen evidencia real.

Casos requeridos:

- `ok`: arribo, movimiento `ING` y DUA confirmados.
- `sin_arribo`: la navegacion debe detenerse y devolver `pending`.
- `madre_hijo_ambiguo`: mas de una seleccion posible; debe devolver `needs_review`.

Antes de guardar un fixture se deben reemplazar manifiestos, conocimientos, DUAs, RUC/cedulas, nombres y cualquier dato sensible, conservando nombres de campos, estructura de tablas, enlaces relativos y estados necesarios para el parser.

Evidencia disponible:

- `ok_hawb/`: ocho pantallas reales, desde el resultado del conocimiento hasta el detalle
  del DUA. El caso produjo arribo, un movimiento `ING`, Detenciones y DUA.
- `sin_stock_mawb/`: resultado, Lineas y Afectaciones reales de un MAWB con arribo que no
  produjo movimiento `ING`.
- `ok.html`: fixture compacto previo, derivado de evidencia PoC.
- `sin_arribo.html` y `madre_hijo_ambiguo.html`: fixtures estructurales sanitizados; no se
  presentan como capturas reales y deben reemplazarse cuando existan casos equivalentes.

Estado de evidencia: TICA-020 se cerro con excepcion aceptada. Entre los conocimientos
entregados no existen casos reales sin fecha de arribo ni multi-ING. `sin_arribo.html`
prueba que un conocimiento existente sin arribo devuelve `pending/arribo_pendiente` y
detiene el recorrido; `madre_hijo_ambiguo.html` prueba `needs_review`. No se presentan
como evidencia real. Cuando existan casos adecuados deben agregarse sus capturas como
regresion.

La herramienta `tools/capturar_fixtures_aereo.py` recibe conocimiento, fecha fin y nombre
del caso. Llama a `page.content()` en cada paso, sanitiza en memoria y escribe solamente
la version depurada. Elimina estados ocultos GeneXus, tokens de navegacion, manifiestos,
conocimientos, DUAs, RUC/cedulas, consignatarios y correos; conserva el DOM, las tablas,
los formatos y la relacion entre filas y enlaces.
