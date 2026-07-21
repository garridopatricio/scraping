# Sprint 5 - QA integral y cierre

## Estado

| Dato | Resultado |
|---|---|
| Estado | En progreso |
| Hito | M5 - QA integral |
| Automatización | Contratos, normalización, API, sesiones terrestres y Livewire cubiertos |
| Pendiente | Validación productiva integral y evidencia manual final |

## Cobertura implementada

- Pruebas Python para modelos, orquestador, estrategias aérea/marítima, API y flujo terrestre.
- Pruebas de formato DUA, aislamiento de sesiones, expiración, límite de sesiones y cierre de recursos.
- Pruebas de CAPTCHA incorrecto, reintentos sobre el mismo desafío, procesamiento asíncrono, polling y cancelación.
- Pruebas Livewire para apertura del modal, estados de carga, errores, persistencia atómica y conservación de observaciones manuales.
- Ruff y mypy forman parte de la verificación técnica del microservicio.

## Matriz operativa

| Escenario | Cobertura actual |
|---|---|
| Consulta aérea completa | Automatizada y validada con fixtures/casos disponibles |
| Consulta marítima normal, anticipada y multilinea | Automatizada y validada con fixtures/casos disponibles |
| DUA terrestre y CAPTCHA manual | Automatizada; pruebas manuales locales realizadas |
| CAPTCHA incorrecto sin regeneración automática | Automatizada |
| Sesión terrestre expirada o cancelada | Automatizada |
| Caída o timeout de TICA | Respuesta controlada; validación productiva pendiente |
| Múltiples movimientos | Normalizados y documentados en Observaciones |

## Riesgos residuales

- TICA es un portal externo GeneXus y puede modificar HTML, enlaces o tiempos de navegación.
- Las sesiones CAPTCHA viven en memoria y deben volver al mismo proceso FastAPI.
- No debe declararse M5 aprobado hasta completar la matriz manual en el ambiente productivo o de QA equivalente.
- Los casos reales disponibles no garantizan todas las combinaciones de líneas, anticipados, detenciones ausentes y múltiples movimientos.

## Criterio de cierre

M5 se aprobará cuando las tres modalidades completen la matriz manual, los campos guardados se contrasten con TICA y los logs no presenten errores pendientes de navegación o persistencia.
