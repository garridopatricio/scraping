# Sprint 6 - Modalidad terrestre

## Estado

| Dato | Resultado |
|---|---|
| Estado | Implementado con validación productiva pendiente |
| Hito | M6 - Terrestre |
| Entrada confirmada | Número DUA |
| Casos de referencia | `002-2026-055881` y `005-2026-470211` |

## Implementado

- Entrada DUA como tres grupos numéricos. Se aceptan guiones o espacios, se eliminan comillas y espacios externos y se normaliza a `aduana-año-correlativo`.
- Sesión Playwright aislada por desafío con identificador opaco, CAPTCHA en memoria, TTL configurable y máximo de tres sesiones activas.
- CAPTCHA manual desde el modal de SD Editar. Un rechazo conserva el desafío y permite reintentar; no genera automáticamente otra imagen.
- Máquina de estados: espera de CAPTCHA, consulta, completado, fallido, expirado y cancelado.
- Después de aceptar el CAPTCHA, FastAPI responde `consultando` y continúa la navegación; Dokka consulta el estado mediante polling.
- Extracción inicial de código DUA, Fecha de Registro, bultos y peso bruto.
- Navegación hacia Manifiesto/Stock, líneas, movimientos y Detenciones para recuperar depósito, ingreso a régimen, fecha/hora, bultos y peso.
- Deduplicación por identificador. Con varios movimientos se publican todos en Observaciones y no se selecciona arbitrariamente depósito o fecha principal.
- Cierre garantizado de página, BrowserContext, navegador y Playwright en éxito, error, cancelación o expiración.

## Integración con Dokka

- Botón **Buscar terrestre** disponible solamente en Shipping Documentation → Editar.
- Modal con CAPTCHA, campo manual, expiración, mensajes de error y estados `Buscando...`/`Consultando...`.
- Actualización única de `arrival_date`, `warehouse_code`, `movement_date`, `package_count`, `total_weight_kg`, `dua_number`, `dua_released_date` y `notes`.
- Los valores confirmados reemplazan los existentes; una respuesta fallida no realiza escrituras parciales.
- El bloque `[TICA INICIO]…[TICA FIN]` se reemplaza sin duplicarse y conserva texto manual antes o después.

## API terrestre

| Método | Ruta | Función |
|---|---|---|
| POST | `/v1/consultas-terrestres` | Crear sesión y obtener CAPTCHA |
| POST | `/v1/consultas-terrestres/{session_id}/resolver` | Resolver CAPTCHA e iniciar extracción |
| GET | `/v1/consultas-terrestres/{session_id}` | Consultar estado y resultado |
| POST | `/v1/consultas-terrestres/{session_id}/regenerar` | Regeneración técnica explícita; no se muestra en la UI actual |
| DELETE | `/v1/consultas-terrestres/{session_id}` | Liberar sesión y recursos temporales |

## Validación pendiente

- Ejecutar la matriz completa en QA/producción con conectividad equivalente al servidor definitivo.
- Contrastar movimientos, detenciones y campos persistidos con TICA en más casos reales.
- Confirmar operación prolongada del daemon, rotación de logs y consumo de recursos.
- M6 permanece pendiente de aprobación formal hasta completar esta evidencia.
