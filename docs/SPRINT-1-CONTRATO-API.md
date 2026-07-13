# Sprint 1 - Revision del contrato API

Revision tecnica aprobada de TICA-018 para el cierre del hito M1.

## Resultado de la revision

El contrato generado por FastAPI coincide con las decisiones vigentes de Sprint 0:

- Entrada unica: `manifiesto` y `fecha_fin`; no recibe modalidad ni cedula.
- La modalidad se publica como `aereo`, `maritimo` o `null` si TICA falla antes de clasificar.
- Los 10 campos requeridos se agrupan en `momento1`, `momento2` y `momento3`.
- `partidas_arancelarias` y `valor_aduanas_impuestos` no forman parte del esquema.
- Se publican los siete estados: `ok`, `pending`, `stale`, `unavailable`, `needs_review`, `not_found` y `not_implemented`.
- El DUA de movilizacion maritimo sigue siendo interno y no aparece en `ResultadoTICA`.
- Las reglas de negocio pendientes pueden expresarse con `pending` o `needs_review` sin inventar datos.

## Request

`POST /v1/consultas`

```json
{
  "manifiesto": "ENGB2600229",
  "fecha_fin": "2026-07-13"
}
```

La fecha usa ISO `YYYY-MM-DD`. Campos faltantes, manifiesto vacio, fecha invalida o campos extra producen HTTP 422 antes de abrir el navegador.

## Response

Todos los resultados de negocio usan HTTP 200 y se distinguen mediante `estado` y `motivo`.

```json
{
  "estado": "pending",
  "modalidad": "maritimo",
  "identificador": "ENGB2600229",
  "momento1": {
    "fecha_arribo": "2026-07-10",
    "transportista": "TRANSPORTISTA"
  },
  "momento2": {
    "movimiento_inventario": null,
    "almacen_fiscal": null,
    "fecha_ingreso_regimen": null,
    "fecha_movimiento_inventario": null,
    "bultos": null,
    "peso_bruto": null
  },
  "momento3": {
    "dua_nacionalizacion": null,
    "fecha_dua": null
  },
  "motivo": "dua_nacionalizacion_pendiente",
  "desde_cache": false,
  "consultado_en": "2026-07-13T12:00:00Z"
}
```

Fechas usan ISO. `bultos` y `peso_bruto` se publican como enteros JSON. El punto mostrado por TICA se interpreta como separador de miles: `3.000` se convierte en `3000`, `614.000` en `614000` y `7450.000` en `7450000`.

## Estados y errores

| Situacion | HTTP | Estado/motivo |
|---|---:|---|
| Resultado completo | 200 | `ok` |
| Sin arribo o sin DUA final | 200 | `pending` |
| Ultima lectura buena por caida posterior | 200 | `stale` |
| Timeout o portal caido sin cache | 200 | `unavailable/portal_unavailable` |
| CAPTCHA | 200 | `unavailable/captcha_required` |
| Modalidad o seleccion ambigua | 200 | `needs_review` |
| Manifiesto no encontrado | 200 | `not_found` |
| Flujo aun no migrado | 200 | `not_implemented` |
| Payload invalido | 422 | Error de validacion FastAPI |
| Portal no disponible en health | 503 | `unavailable` |

## Health checks

- `GET /v1/health`: confirma que FastAPI responde; HTTP 200.
- `GET /v1/health/portal`: comprueba solamente la portada de TICA; HTTP 200 o 503.

## Decisiones aprobadas para M1

1. `bultos` y `peso_bruto` son enteros JSON; los puntos de TICA son separadores de miles.
2. Los estados de negocio se mantienen en HTTP 200 y el consumidor decide usando `estado`.
3. El catalogo de estados vigente tiene siete valores, pero podra modificarse o ampliarse mediante futuras versiones del contrato.
4. Las reglas abiertas de multiples movimientos, varias lineas y pedidos anticipados no cambian la forma del contrato; se resolveran en Sprint 2/3 mediante valores, `pending` o `needs_review`.

Estado de TICA-018: aprobada. Hito M1 cerrado el 2026-07-13.
