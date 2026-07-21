# Integración de aplicaciones con Scrapping TICA API

## Propósito

Esta guía define cómo cualquier aplicación backend puede solicitar información a Scrapping TICA. El servicio navega TICA, normaliza la respuesta y administra recursos Playwright; el consumidor autentica a sus usuarios, presenta estados/CAPTCHA y persiste los datos que correspondan.

## Aéreo y marítimo

`POST /v1/consultas` recibe entre 1 y 100 conocimientos y una fecha final:

```json
{
  "manifiestos": ["BL-1416-3924", "123-456789"],
  "fecha_fin": "2026-07-20"
}
```

Cada clave de la respuesta corresponde al identificador solicitado. La modalidad se detecta en TICA y el resultado incluye `estado`, `modalidad`, `momento1`, `momento2`, `momento3`, `motivo` y `desde_cache`.

Los elementos se procesan secuencialmente. Un fallo individual no cancela el resto del lote. El cliente debe aplicar un timeout compatible con la navegación y evitar reintentos paralelos inmediatos.

## Terrestre y CAPTCHA

1. Crear desafío:

   `POST /v1/consultas-terrestres` con `{ "dua": "005-2026-470211" }`.

2. Mostrar al usuario la imagen base64 y expiración devueltas.
3. Resolver con `POST /v1/consultas-terrestres/{session_id}/resolver` y `{ "captcha": "texto" }`.
4. Si responde `captcha_incorrecto`, conservar la imagen, limpiar el campo y permitir otro intento.
5. Si responde `consultando`, consultar periódicamente `GET /v1/consultas-terrestres/{session_id}`.
6. Consumir el resultado únicamente cuando el estado sea `completado`.
7. En éxito, cancelación o cierre, enviar `DELETE` para liberar recursos.

El `session_id` es opaco. El consumidor no debe interpretarlo, compartirlo entre usuarios ni persistirlo como dato del negocio. Una sesión expirada no se puede reanudar.

## Persistencia e idempotencia

- La API no escribe en la base del consumidor.
- El consumidor debe validar que el resultado corresponde al identificador solicitado y realizar una actualización atómica.
- Valores vacíos o respuestas fallidas no deberían borrar información previa.
- Con múltiples movimientos no debe elegirse arbitrariamente uno para campos ambiguos; puede conservarse la colección completa.
- El cliente debe reemplazar su bloque de información automática en vez de concatenarlo en cada consulta.

## Estados y errores

- `ok`/`completado`: resultado utilizable.
- `pending`: TICA aún no contiene toda la información.
- `not_found`: búsqueda ejecutada sin coincidencias.
- `needs_review`: resultado ambiguo.
- `unavailable`, `stale` o `fallido`: degradación o error controlado.
- `expirado`/`cancelado`: sesión terrestre terminada.

Los códigos HTTP describen el transporte; un HTTP 200 puede contener un estado de negocio como `not_found`. Use `correlacion_id` para seguimiento operativo y no exponga excepciones técnicas al usuario final.

## Seguridad actual

La versión actual no implementa autenticación de clientes ni aislamiento por tenant. Debe publicarse en una red privada o detrás de un gateway/reverse proxy con controles de acceso. El navegador no debería llamar directamente al scraper: la aplicación backend debe actuar como cliente confiable.

## RAGA Orders/Dokka como referencia

RAGA consume la API desde Laravel. **Buscar DUA** usa el contrato aéreo/marítimo; **Buscar terrestre** muestra el CAPTCHA y realiza polling. Laravel decide el `ShippingDocument`, aplica reglas por `company_id`, persiste los campos y conserva Observaciones manuales. Ninguna de esas responsabilidades pertenece al scraper.

## Evolución multitenant

RAGA identifica actualmente empresas mediante `company_id`, pero Scrapping TICA todavía no recibe ni valida tenants. Antes de ofrecer la API como servicio multitenant se deberá decidir:

- autenticación y autorización entre servicios;
- forma validada de derivar el tenant;
- cuotas, concurrencia y rate limits por tenant;
- aislamiento de caché, sesiones CAPTCHA y logs;
- auditoría, retención y protección de identificadores;
- afinidad o estado compartido para múltiples workers.

No se define todavía API key, JWT, OAuth ni un header de tenant. Un futuro diseño nunca debe confiar en un tenant enviado libremente por el navegador sin validación del backend.
