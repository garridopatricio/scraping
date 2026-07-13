# Fixtures aereos

Esta carpeta contendra HTML sanitizado derivado de casos reales ya confirmados por la PoC.

Casos requeridos:

- `ok`: arribo, movimiento `ING` y DUA confirmados.
- `sin_arribo`: la navegacion debe detenerse y devolver `pending`.
- `madre_hijo_ambiguo`: mas de una seleccion posible; debe devolver `needs_review`.

Antes de guardar un fixture se deben reemplazar manifiestos, conocimientos, DUAs, RUC/cedulas, nombres y cualquier dato sensible, conservando nombres de campos, estructura de tablas, enlaces relativos y estados necesarios para el parser.

No crear HTML inventado ni copiar reportes Markdown como si fueran respuestas del portal.
