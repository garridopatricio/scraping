# Fixtures maritimos

HTML derivados de capturas reales de TICA y sanitizados antes de guardarse.

| Carpeta | Tipo | Cobertura |
|---|---|---|
| `normal_una_linea` | Real | Nueve pantallas, un movimiento y DUA final. |
| `anticipado` | Real | Cinco pantallas; se detiene antes de Depositos. |
| `consolidado_multilinea` | Real | Dos lineas, movimientos/Detenciones por linea y DUA consolidado. |

La sanitizacion reemplaza conocimientos, manifiestos, cedulas, DUAs, movimientos,
nombres, razones sociales, correos, tokens y estados ocultos GeneXus. Se conservan la
estructura DOM, relacion fila-enlace, estado `ING`, fechas y cantidades representativas.

Los tests son offline. Para renovar evidencia se usa
`tools/capturar_fixtures_maritimo.py`; nunca debe versionarse el HTML crudo.
