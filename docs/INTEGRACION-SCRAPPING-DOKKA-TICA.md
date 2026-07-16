# Integracion automatica Scrapping DOKKA-TICA

## Objetivo

DOKKA consulta automaticamente TICA con el HBL o guia hija de cada `ShippingDocument`.
FastAPI permanece como proceso Python independiente dentro de
`dokka-orders-raga/scrapping-tica/`, mientras Laravel controla seleccion, cola,
persistencia y horario.

## Persistencia sin cambios de esquema

No se crean tablas, migraciones ni columnas. Solo se modifican campos existentes de
`shipping_documents`:

- `dua_number`: primer DUA no vacio segun el orden de las guias hijas.
- `dua_released_date`: fecha correspondiente al primer DUA.
- `notes`: detalle completo y metadatos de sincronizacion.

Los valores anteriores de DUA y fecha nunca se borran por una respuesta `pending`,
`not_found`, `needs_review`, `stale` o `unavailable`.

## Identificadores

1. Se usa `bill_of_lading_child_number`.
2. Si esta vacio, se usa `hbl_number` como respaldo.
3. Comas, punto y coma y saltos de linea separan varias guias.
4. Se eliminan vacios y duplicados conservando el orden.

No se consultan MBL, BL master, booking, contenedor ni tracking.

## Bloque de observaciones

Las notas manuales se preservan. Laravel reemplaza solamente:

```text
[TICA INICIO]
Ultima consulta: 2026-07-15T22:00:00+00:00
Intento: 1
Estado general: complete|pending|review_manual

Conocimiento: HBL
Estado: ok|pending|...
Motivo: ...
Modalidad: aereo|maritimo
Fecha arribo: ...
Transportista: ...
Movimiento: ...
Almacen: ...
Fecha ingreso regimen: ...
Fecha movimiento: ...
Bultos: ...
Peso bruto: ...
DUA: ...
Fecha DUA: ...
[TICA FIN]
```

Con varias guias o movimientos se detalla cada resultado. Los campos unicos del SD
representan solamente el primer DUA; los demas quedan en `notes`.

## Ejecucion

- Local: al entrar en `Embarques`, un componente Livewire encola SD incompletos y muestra
  progreso sin bloquear la pagina.
- Produccion: `tica:sync` se ejecuta cada hora con `withoutOverlapping()`.
- Cada SD usa un Job en la cola `tica-sync`. Produccion debe ejecutar un solo worker de
  esa cola para respetar TICA.
- Un SD completo deja de consultarse. Los demas se reintentan cada hora hasta 72 intentos;
  luego `notes` indica `review_manual`.
- Actualmente no se filtra por estado del SD. La seleccion por estado queda configurable
  para una regla futura.

Comandos locales:

```powershell
& ".\scrapping-tica\.venv\Scripts\python.exe" -m uvicorn app.main:app `
  --app-dir ".\scrapping-tica"
php artisan tica:sync --force
php artisan queue:work database --queue=tica-sync --timeout=900 --tries=1
```

En produccion deben mantenerse activos Laravel, scheduler, un worker `tica-sync`, FastAPI,
Playwright y Chromium.

## QA local 2026-07-15

Se procesaron 8 SD reales de prueba: cinco aereos y tres maritimos. Todos finalizaron
`complete`, actualizaron `dua_number`/`dua_released_date` y escribieron el bloque TICA.
El consolidado maritimo con dos movimientos conservo ambos en observaciones.
