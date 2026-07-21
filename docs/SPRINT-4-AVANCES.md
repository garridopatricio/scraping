# Sprint 4 - Integración de clientes con la API

## Estado

| Dato | Resultado |
|---|---|
| Estado | Implementado localmente; validación productiva pendiente |
| Hito | M4 - Integracion RAGA |
| Tareas | TICA-040 a TICA-042 completadas |
| Base de datos | Sin tablas, migraciones ni columnas nuevas |
| QA | 8 SD sincronizados con TICA real |

## Implementado

- Scraper integrado dentro de DOKKA como proceso FastAPI separado.
- Cliente Laravel, resolver de guia hija/HBL y mapper invocados por el boton **Buscar DUA**.
- El resolver Laravel elimina comillas simples o dobles envolventes de los BL; FastAPI
  aplica la misma normalizacion antes de navegar TICA para proteger todos los clientes.
- Aéreo/marítimo mantiene la consulta manual síncrona. Terrestre devuelve `consultando` después del CAPTCHA y usa polling para evitar mantener una petición PHP durante toda la navegación.
- Refresco Livewire inmediato de los campos pareados sin recargar la pagina.
- Persistencia en campos existentes: `arrival_date`, `warehouse_code`, `movement_date`, `package_count`, `total_weight_kg`, `dua_number`, `dua_released_date` y `notes`.
- Las notas conservan transportista, movimiento de inventario, fecha de ingreso a regimen, almacen completo, timestamp completo y movimientos multilinea; no duplican valores completamente pareados.
- Los valores no vacios reemplazan los existentes y los valores nulos no borran informacion.
- Se documenta que fecha de arribo, ingreso al regimen y movimiento son tres marcas distintas; solo arribo y la fecha del movimiento tienen destino estructurado.
- Bultos permanece entero. Peso admite decimales y Dokka lo persiste como `decimal(10,2)`.
- **Buscar terrestre** está disponible únicamente en SD Editar y abre un modal de CAPTCHA manual.
- Al iniciar una búsqueda se limpia el mensaje anterior. La actualización se realiza una sola vez después de recibir un resultado completo.
- El bloque `[TICA INICIO]…[TICA FIN]` se reemplaza sin duplicarse y conserva observaciones manuales fuera de sus delimitadores.

## Evidencia QA

Los 8 SD locales con guia hija finalizaron `complete`. Se reemplazaron los DUAs ficticios
por datos TICA y se verifico directamente PostgreSQL. El detalle se encuentra en
`INTEGRACION-API-TICA.md`.

## Pendiente operativo

- Definir URL y supervision de FastAPI en QA/produccion.
- Validar el pareo actualizado con casos reales en QA/produccion.
- Resolver en una fase futura si transportista corresponde a `shipping_documents.carrier_name` o `purchase_orders.carrier`.
- Definir campos propios solo si Dokka necesita sacar movimiento de inventario o fecha de ingreso al regimen de observaciones.
- Crear rama, commit y despliegue solo cuando sean solicitados.
