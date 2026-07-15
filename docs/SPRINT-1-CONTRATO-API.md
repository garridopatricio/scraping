# Contrato API - Consultas TICA

Contrato aprobado en M1 y actualizado el 2026-07-14 para admitir uno o varios manifiestos por solicitud.

## Endpoint

`POST /v1/consultas`

La ruta es la misma para uno o varios manifiestos. La forma del request y del response tambien es siempre la misma.

## Request

```json
{
  "manifiestos": ["MANIFIESTO-A", "MANIFIESTO-B"],
  "fecha_fin": "2026-07-14"
}
```

Para consultar uno solo igualmente se envia una lista:

```json
{
  "manifiestos": ["MANIFIESTO-A"],
  "fecha_fin": "2026-07-14"
}
```

`manifiesto` conserva el significado que ya tiene en las reglas del proyecto: es el identificador con el que comienza la busqueda del conocimiento. No se agrega una entidad generica llamada `codigo`.

`fecha_inicio` es opcional. Al omitirla, el servicio no completa el campo de inicio y conserva el mismo comportamiento de la pantalla manual de TICA:

```json
{
  "manifiestos": ["MANIFIESTO-A"],
  "fecha_fin": "2026-07-14"
}
```

Cuando se necesite limitar la busqueda, puede enviarse explicitamente:

```json
{
  "manifiestos": ["MANIFIESTO-A"],
  "fecha_inicio": "2026-07-01",
  "fecha_fin": "2026-07-14"
}
```

## Reglas del lote

1. Se aceptan entre 1 y 100 manifiestos unicos por solicitud.
2. Todos usan la misma `fecha_fin` y, cuando se envia, la misma `fecha_inicio`.
3. Los manifiestos se procesan secuencialmente, en el orden recibido.
4. No se crean tareas paralelas contra TICA.
5. Un resultado fallido no detiene los manifiestos siguientes.
6. Manifiestos vacios, repetidos o una lista mayor a 100 producen HTTP 422.
7. No se recibe modalidad; cada manifiesto se clasifica desde `Desc Descarga` de Master.
8. `fecha_inicio` no puede ser posterior a `fecha_fin`; cuando existe, la ventana inclusiva no puede superar 15 dias.
9. Si `fecha_inicio` se omite, queda vacia en TICA y no se calcula automaticamente restando 14 dias.

Aunque FastAPI y Playwright son asincronos, la iteracion del lote es secuencial. `await` permite esperar I/O sin bloquear innecesariamente el servidor, pero el manifiesto siguiente no inicia hasta terminar el anterior. Esta regla reduce carga sobre el portal publico, evita mezclar sesiones y coincide con la serializacion de `BrowserManager`.

El limite 100 es una proteccion para un endpoint HTTP sincronico, no una restriccion del concepto de manifiesto. Si mas adelante se necesitan lotes mayores, se deben dividir en solicitudes de hasta 100 o implementar un trabajo en segundo plano con seguimiento de estado. Un lote grande puede tardar varios minutos, por lo que el cliente debe configurar un timeout acorde.

## Response

La respuesta es un objeto JSON cuya clave de primer nivel es cada manifiesto recibido. Bajo esa clave aparecen directamente los datos de la consulta:

```json
{
  "MANIFIESTO-A": {
    "estado": "pending",
    "modalidad": "aereo",
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
      "peso_bruto": null,
      "movimientos": []
    },
    "momento3": {
      "dua_nacionalizacion": null,
      "fecha_dua": null
    },
    "motivo": "dua_nacionalizacion_pendiente",
    "desde_cache": false,
    "consultado_en": "2026-07-14T12:00:00Z"
  },
  "MANIFIESTO-B": {
    "estado": "not_found",
    "modalidad": null,
    "momento1": {
      "fecha_arribo": null,
      "transportista": null
    },
    "momento2": {
      "movimiento_inventario": null,
      "almacen_fiscal": null,
      "fecha_ingreso_regimen": null,
      "fecha_movimiento_inventario": null,
      "bultos": null,
      "peso_bruto": null,
      "movimientos": []
    },
    "momento3": {
      "dua_nacionalizacion": null,
      "fecha_dua": null
    },
    "motivo": "manifiesto_no_encontrado",
    "desde_cache": false,
    "consultado_en": "2026-07-14T12:00:10Z"
  }
}
```

El manifiesto recibido se usa como clave y no se repite dentro de sus datos. Tampoco se exponen el nombre interno `identificador` ni los envoltorios `regla` y `resultados`.

## Campos de cada resultado

Los 10 campos escalares vigentes se conservan y se agrega una coleccion tipada:

- Momento 1: `fecha_arribo`, `transportista`.
- Momento 2: `movimiento_inventario`, `almacen_fiscal`, `fecha_ingreso_regimen`, `fecha_movimiento_inventario`, `bultos`, `peso_bruto` y `movimientos`.
- Momento 3: `dua_nacionalizacion`, `fecha_dua`.

`partidas_arancelarias` y `valor_aduanas_impuestos` permanecen fuera del esquema. El DUA de movilizacion maritimo sigue siendo interno.

En maritimo, `movimientos` contiene todos los movimientos de las lineas. Con uno solo,
los campos escalares conservan el mismo valor por compatibilidad; con varios, los
escalares quedan `null`. Aereo siempre entrega `movimientos: []`.

`bultos` y `peso_bruto` son enteros JSON. TICA presenta tres decimales: `3.000` se
normaliza como `3`. Esta interpretacion fue corregida durante el QA maritimo al comparar
los movimientos por linea con el total consolidado.

## Estados y aislamiento

Cada manifiesto tiene su propio `estado`, `motivo`, modalidad, datos y timestamp:

| Situacion | Estado/motivo |
|---|---|
| Resultado completo | `ok` |
| Conocimiento encontrado, pero sin fecha de arribo | `pending/arribo_pendiente` |
| Conocimiento con arribo, pero sin DUA final | `pending` |
| Lectura anterior por caida posterior | `stale` |
| Portal caido sin cache | `unavailable/portal_unavailable` |
| CAPTCHA | `unavailable/captcha_required` |
| Seleccion ambigua | `needs_review` |
| Manifiesto no encontrado | `not_found/manifiesto_no_encontrado` |
| Flujo aun no migrado | `not_implemented` |
| Excepcion inesperada aislada por el lote | `unavailable/error_interno_manifiesto` |

Los resultados de negocio usan HTTP 200 y el consumidor decide mediante el estado de cada elemento. El catalogo podra evolucionar mediante futuras actualizaciones del contrato.

## Errores HTTP

| Situacion | HTTP |
|---|---:|
| Lote valido, aunque algunos manifiestos fallen | 200 |
| Payload invalido, duplicados, mas de 100 manifiestos o ventana explicita de fechas invalida | 422 |
| `GET /v1/health` disponible | 200 |
| `GET /v1/health/portal` disponible | 200 |
| Portal no disponible en health | 503 |

## Cambio respecto del contrato inicial

El contrato inicial recibia `manifiesto` y devolvia un solo `ResultadoTICA`. Desde el 2026-07-14:

- El request publico usa `manifiestos`, una lista del mismo identificador ya definido en el proyecto.
- `fecha_inicio` pasa a ser opcional; su ausencia conserva el campo vacio de TICA.
- La lista se utiliza incluso para un solo manifiesto.
- La respuesta usa cada manifiesto como clave de primer nivel.
- Bajo cada clave aparecen directamente los datos solicitados, sin `regla` ni `resultados`.
- El orquestador unitario se conserva internamente y se invoca una vez por manifiesto.
