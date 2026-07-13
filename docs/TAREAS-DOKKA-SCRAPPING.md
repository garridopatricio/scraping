# Tareas — Proyecto Dokka Scrapping

> **Cliente:** Grupo Dokka / Central Farmacéutica  
> **Descripción:** Automatización de consultas al portal TICA para obtener datos oficiales de importación e integrarlos con RAGA Orders mediante un microservicio de scraping y API REST.  
> **PM:** Francisco Espinoza · **Etapa:** Planificación · **Complejidad general:** Alta  
> **Total de tareas:** 41  
> _Exportado desde Notion — base de datos "Tareas"._

---

## Resumen por sprint

| Sprint | Tareas | Horas estimadas |
|---|---|---|
| Sprint 0 - PoC y planificación | 6 | 14 |
| Sprint 1 - Infra base | 9 | 34 |
| Sprint 2 - Modalidad aérea | 7 | 27 |
| Sprint 3 - Modalidad marítima | 7 | 36 |
| Sprint 4 - Integración RAGA Orders | 3 | 12 |
| Sprint 5 - QA integral y cierre | 4 | 18 |
| Sprint 6 - Terrestre condicional | 5 | 20 |
| **Total** | **41** | **161** |

## Resumen por estado

| Estado | Tareas |
|---|---|
| Done | 6 |
| Pending | 35 |

---

## Sprint 0 - PoC y planificación

### TICA-001 - Solicitar caso aéreo real
- **Estado:** Done · **Prioridad:** Crítica · **Complejidad:** Baja
- **Tipo:** Documentación · **Tipo de tarea:** Mejoras · **Estimación:** 0 h
- **Responsable:** Francisco Espinoza, Daniel Balieiro
- **Fecha asignación:** 2026-07-06 · **Fecha entrega:** 2026-07-06 · **PR/QA:** Sí
- **Descripción:** Solicitar a Dokka un caso aéreo real para validar PoC y fixtures.
- **Entregable esperado:** Caso aéreo documentado.
- **Criterios de aceptación:** Caso recibido con guía, fecha aproximada y DUA liberado.
- **Notas funcionales:** Bloquea F0 y F2.
- **Notas técnicas:** Debe evitar datos innecesariamente sensibles.

### TICA-002 - Solicitar caso marítimo real
- **Estado:** Done · **Prioridad:** Crítica · **Complejidad:** Baja
- **Tipo:** Documentación · **Tipo de tarea:** Mejoras · **Estimación:** 0 h
- **Responsable:** Francisco Espinoza, Daniel Balieiro
- **Fecha asignación:** 2026-07-06 · **Fecha entrega:** 2026-07-06 · **PR/QA:** Sí
- **Descripción:** Solicitar a Dokka un caso marítimo real para validar PoC y fixtures.
- **Entregable esperado:** Caso marítimo documentado.
- **Criterios de aceptación:** Caso recibido con BL, cédula jurídica, fecha y DUA liberado.
- **Notas funcionales:** Bloquea F0 y F3.
- **Notas técnicas:** Debe incluir cédula jurídica correcta.

### TICA-003 - Construir script PoC Playwright
- **Estado:** Done · **Prioridad:** Crítica · **Complejidad:** Media
- **Tipo:** Demo · **Tipo de tarea:** Desarrollo · **Estimación:** 6 h
- **Responsable:** patricio garrido
- **Fecha asignación:** 2026-07-08 · **Fecha entrega:** 2026-07-10 · **PR/QA:** Sí
- **Descripción:** Crear script desechable para navegar TICA con casos reales.
- **Entregable esperado:** Script de PoC.
- **Criterios de aceptación:** Script corre por variables de entorno y registra login/CAPTCHA/campos visibles.
- **Notas funcionales:** No intenta resolver CAPTCHA.
- **Notas técnicas:** Playwright Chromium, headless configurable.

### TICA-004 - Ejecutar PoC con casos reales
- **Estado:** Done · **Prioridad:** Crítica · **Complejidad:** Media
- **Tipo:** Demo · **Tipo de tarea:** Mejoras · **Estimación:** 2 h
- **Responsable:** —
- **Fecha asignación:** 2026-07-08 · **Fecha entrega:** 2026-07-10 · **PR/QA:** Sí
- **Descripción:** Ejecutar PoC y registrar resultados.
- **Entregable esperado:** Resultado de ejecución.
- **Criterios de aceptación:** Matriz de visibilidad completada para campos requeridos.
- **Notas funcionales:** Define gate M0.
- **Notas técnicas:** No hardcodear credenciales.

### TICA-005 - Documentar poc_resultado.md
- **Estado:** Done · **Prioridad:** Crítica · **Complejidad:** Baja
- **Tipo:** Documentación · **Tipo de tarea:** Mejoras · **Estimación:** 2 h
- **Responsable:** Francisco Espinoza, patricio garrido
- **Fecha asignación:** 2026-07-09 · **Fecha entrega:** 2026-07-17 · **PR/QA:** Sí
- **Descripción:** Crear reporte de hallazgos de PoC.
- **Entregable esperado:** poc_resultado.md.
- **Criterios de aceptación:** Documento indica público/login/no disponible por campo.
- **Notas funcionales:** Campo valor/impuestos debe quedar explícito.
- **Notas técnicas:** Fuera de git si contiene datos sensibles.

### TICA-006 - Revisar PoC con QA
- **Estado:** Done · **Prioridad:** Crítica · **Complejidad:** Baja
- **Tipo:** Demo · **Tipo de tarea:** Mejoras · **Estimación:** 2 h
- **Responsable:** patricio garrido
- **Fecha asignación:** 2026-07-09 · **Fecha entrega:** 2026-07-10 · **PR/QA:** Sí
- **Descripción:** Contrastar hallazgos con documento de proceso TICA.
- **Entregable esperado:** Gate M0 aprobado.
- **Criterios de aceptación:** QA aprueba o levanta observaciones del gate M0.
- **Notas funcionales:** Sin M0 no cerrar alcance.
- **Notas técnicas:** Usar evidencia de PoC.

---

## Sprint 1 - Infra base

### TICA-010 - Scaffold microservicio Python
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Infraestructura · **Tipo de tarea:** Arquitectura · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Crear pyproject, config y estructura app.
- **Entregable esperado:** Scaffold inicial.
- **Criterios de aceptación:** Estructura importa sin error y dependencias declaradas.
- **Notas funcionales:** Base del servicio.
- **Notas técnicas:** Python 3.12, FastAPI, Pydantic, Playwright.

### TICA-011 - Modelos Pydantic y enums
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Backend · **Tipo de tarea:** Arquitectura · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Implementar ConsultaInput, ResultadoTICA y modelos por momento.
- **Entregable esperado:** Modelos de dominio.
- **Criterios de aceptación:** Modelos validan y serializan; estados completos.
- **Notas funcionales:** Debe soportar tres modalidades.
- **Notas técnicas:** Pydantic v2.

### TICA-012 - Gestor navegador con backoff
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Alta
- **Tipo:** Infraestructura · **Tipo de tarea:** Desarrollo · **Estimación:** 6 h · **PR/QA:** Sí
- **Descripción:** Implementar browser manager async.
- **Entregable esperado:** app/scraper/browser.py.
- **Criterios de aceptación:** Reintentos controlados y salida unavailable sin excepción cruda.
- **Notas funcionales:** Evitar paralelismo agresivo contra TICA.
- **Notas técnicas:** Context manager async.

### TICA-013 - Interfaz estrategia modalidad
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Baja
- **Tipo:** Backend · **Tipo de tarea:** Arquitectura · **Estimación:** 2 h · **PR/QA:** Sí
- **Descripción:** Crear base y stubs aéreo/marítimo/terrestre.
- **Entregable esperado:** Estrategias iniciales.
- **Criterios de aceptación:** Orquestador puede despachar por modalidad.
- **Notas funcionales:** Terrestre retorna not_implemented.
- **Notas técnicas:** Patrón estrategia.

### TICA-014 - Orquestador de consultas
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Alta
- **Tipo:** Backend · **Tipo de tarea:** Arquitectura · **Estimación:** 8 h · **PR/QA:** Sí
- **Descripción:** Implementar lógica central de consulta.
- **Entregable esperado:** app/orchestrator/consulta.py.
- **Criterios de aceptación:** Valida entrada, ventana 15 días, estados, cache y reintentos.
- **Notas funcionales:** Entrada inválida no abre navegador.
- **Notas técnicas:** Mapear excepciones a estados.

### TICA-015 - Cache última lectura buena
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Infraestructura · **Tipo de tarea:** Desarrollo · **Estimación:** 3 h · **PR/QA:** Sí
- **Descripción:** Implementar cache en memoria migrable a Redis.
- **Entregable esperado:** app/cache/store.py.
- **Criterios de aceptación:** Guarda y recupera ResultadoTICA con TTL.
- **Notas funcionales:** Habilita estado stale.
- **Notas técnicas:** Key por modalidad e identificador.

### TICA-016 - Logging estructurado
- **Estado:** Pending · **Prioridad:** Media · **Complejidad:** Baja
- **Tipo:** Infraestructura · **Tipo de tarea:** Desarrollo · **Estimación:** 1 h · **PR/QA:** Sí
- **Descripción:** Configurar structlog.
- **Entregable esperado:** app/observability/logging.py.
- **Criterios de aceptación:** Cada consulta emite JSON con modalidad, estado y duración.
- **Notas funcionales:** Ayuda a soporte operativo.
- **Notas técnicas:** Logs sin datos sensibles innecesarios.

### TICA-017 - API FastAPI y health
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 2 h · **PR/QA:** Sí
- **Descripción:** Crear rutas y main.
- **Entregable esperado:** API inicial.
- **Criterios de aceptación:** POST /v1/consultas valida; health responde 200.
- **Notas funcionales:** Contrato para RAGA Orders.
- **Notas técnicas:** Tests de humo.

### TICA-018 - Revisión contrato API
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Baja
- **Tipo:** Demo · **Tipo de tarea:** Mejoras · **Estimación:** 2 h · **PR/QA:** Sí
- **Descripción:** Revisar payloads, errores y estados.
- **Entregable esperado:** M1 aprobado.
- **Criterios de aceptación:** QA valida contrato y estados antes de F2/F3.
- **Notas funcionales:** Bloquea integración.
- **Notas técnicas:** Usar ejemplos de request/response.

---

## Sprint 2 - Modalidad aérea

### TICA-020 - Fixtures flujo aéreo
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Backend · **Tipo de tarea:** Mejoras · **Estimación:** 3 h · **PR/QA:** Sí
- **Descripción:** Guardar HTML representativo del flujo aéreo.
- **Entregable esperado:** tests/fixtures/aereo.
- **Criterios de aceptación:** Fixtures cubren ok, sin arribo y ambigüedad madre/hijo.
- **Notas funcionales:** Sin datos sensibles extra.
- **Notas técnicas:** Tests no tocan TICA vivo.

### TICA-021 - Aéreo Momento 1 arribo
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 3 h · **PR/QA:** Sí
- **Descripción:** Implementar consulta inicial aérea.
- **Entregable esperado:** Parser momento 1.
- **Criterios de aceptación:** Devuelve fecha arribo y transportista; sin arribo pending.
- **Notas funcionales:** Fecha TICA prevalece.
- **Notas técnicas:** Tests contra fixtures.

### TICA-022 - Aéreo Momento 2 movimiento ING
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Alta
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 6 h · **PR/QA:** Sí
- **Descripción:** Implementar Líneas y Afectaciones.
- **Entregable esperado:** Parser momento 2.
- **Criterios de aceptación:** Filtra ING y captura movimiento, almacén, fechas, bultos y peso.
- **Notas funcionales:** Fechas no se colapsan.
- **Notas técnicas:** Tests contra fixtures.

### TICA-023 - Regla madre/hijo aéreo
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Implementar selección segura de movimiento.
- **Entregable esperado:** Regla de selección.
- **Criterios de aceptación:** Ambigüedad retorna needs_review.
- **Notas funcionales:** No adivinar.
- **Notas técnicas:** Test dedicado.

### TICA-024 - Aéreo Momento 3 DUA
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 3 h · **PR/QA:** Sí
- **Descripción:** Implementar parser de DUA aéreo.
- **Entregable esperado:** Parser momento 3.
- **Criterios de aceptación:** Captura DUA, fecha, partidas y valor si visible; sin DUA pending.
- **Notas funcionales:** Partidas como lista.
- **Notas técnicas:** Tests contra fixtures.

### TICA-025 - Tests aéreos
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Demo · **Tipo de tarea:** Mejoras · **Estimación:** 3 h · **PR/QA:** Sí
- **Descripción:** Crear/ejecutar pruebas de modalidad aérea.
- **Entregable esperado:** Suite aérea.
- **Criterios de aceptación:** Casos ok, pending y needs_review en verde.
- **Notas funcionales:** Ningún test contra TICA vivo.
- **Notas técnicas:** Fixtures HTML.

### TICA-026 - Validación QA aérea
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Baja
- **Tipo:** Demo · **Tipo de tarea:** Mejoras · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Revisar datos contra evidencia cliente.
- **Entregable esperado:** M2 aprobado.
- **Criterios de aceptación:** QA valida flujo aéreo con caso real.
- **Notas funcionales:** Requiere contraparte si hay dudas.
- **Notas técnicas:** Comparar con reporte manual.

---

## Sprint 3 - Modalidad marítima

### TICA-030 - Fixtures flujo marítimo
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Backend · **Tipo de tarea:** Mejoras · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Guardar HTML de los 9 pasos.
- **Entregable esperado:** tests/fixtures/maritimo.
- **Criterios de aceptación:** Fixtures cubren flujo completo y consolidado multi-cédula.
- **Notas funcionales:** Datos sensibles mínimos.
- **Notas técnicas:** Tests no tocan TICA vivo.

### TICA-031 - Marítimo DUA movilización
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Alta
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 6 h · **PR/QA:** Sí
- **Descripción:** Implementar pasos conocimiento y Líneas/Afectaciones.
- **Entregable esperado:** Parser DUA movilización.
- **Criterios de aceptación:** DUA inicial queda marcado como movilización.
- **Notas funcionales:** No es nacionalización.
- **Notas técnicas:** Campo interno separado.

### TICA-032 - Marítimo depósitos
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Alta
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 6 h · **PR/QA:** Sí
- **Descripción:** Implementar navegación a depósitos.
- **Entregable esperado:** Parser depósitos.
- **Criterios de aceptación:** Usa depósito, fecha y DUA de movilización para buscar inventario.
- **Notas funcionales:** No ir directo a DUAs en este paso.
- **Notas técnicas:** Tests con fixtures.

### TICA-033 - Filtro por cédula jurídica
- **Estado:** Pending · **Prioridad:** Crítica · **Complejidad:** Alta
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Filtrar consolidado por cédula del input.
- **Entregable esperado:** Regla cédula.
- **Criterios de aceptación:** Si cédula no aparece retorna not_found.
- **Notas funcionales:** Evita datos de otra empresa.
- **Notas técnicas:** Test multi-cédula.

### TICA-034 - DUA nacionalización marítimo
- **Estado:** Pending · **Prioridad:** Crítica · **Complejidad:** Alta
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 6 h · **PR/QA:** Sí
- **Descripción:** Implementar consulta final en depósitos.
- **Entregable esperado:** Parser DUA nacionalización.
- **Criterios de aceptación:** Solo devuelve DUA nacionalización confirmado; si no pending.
- **Notas funcionales:** Regla crítica de negocio.
- **Notas técnicas:** Test bloqueante.

### TICA-035 - Tests marítimos regla dura
- **Estado:** Pending · **Prioridad:** Crítica · **Complejidad:** Media
- **Tipo:** Demo · **Tipo de tarea:** Mejoras · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Crear suite marítima completa.
- **Entregable esperado:** Suite marítima.
- **Criterios de aceptación:** Test falla si DUA movilización se reporta como nacionalización.
- **Notas funcionales:** Incluye consolidado multi-cédula.
- **Notas técnicas:** Fixtures HTML.

### TICA-036 - Validación QA marítima
- **Estado:** Pending · **Prioridad:** Crítica · **Complejidad:** Baja
- **Tipo:** Demo · **Tipo de tarea:** Mejoras · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Revisar datos contra evidencia cliente.
- **Entregable esperado:** M3 aprobado.
- **Criterios de aceptación:** QA valida flujo marítimo con caso real.
- **Notas funcionales:** Riesgo alto si hay error de DUA.
- **Notas técnicas:** Comparar con reporte manual.

---

## Sprint 4 - Integración RAGA Orders

### TICA-040 - Campos RAGA Orders
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Modificar modelo de embarques.
- **Entregable esperado:** Migraciones y modelos.
- **Criterios de aceptación:** Agrega DMS, cédula jurídica y múltiples conocimientos sin romper datos.
- **Notas funcionales:** Base para modalidades.
- **Notas técnicas:** Laravel/RAGA Orders.

### TICA-041 - UI datos TICA en orden
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Frontend · **Tipo de tarea:** Desarrollo · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Agregar bloque de datos TICA en detalle.
- **Entregable esperado:** UI funcional.
- **Criterios de aceptación:** Vista muestra datos y estados; needs_review destacado.
- **Notas funcionales:** No romper vista con timeout.
- **Notas técnicas:** Inertia/React según RAGA.

### TICA-042 - Cliente HTTP servicio TICA
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Full Stack · **Tipo de tarea:** Desarrollo · **Estimación:** 4 h · **PR/QA:** Sí
- **Descripción:** Consumir POST /v1/consultas desde RAGA.
- **Entregable esperado:** Cliente integrado.
- **Criterios de aceptación:** Maneja los 7 estados y refresh sin recarga manual.
- **Notas funcionales:** Depende del contrato F1.
- **Notas técnicas:** Timeouts controlados.

---

## Sprint 5 - QA integral y cierre

### TICA-050 - Matriz QA de estados
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Demo · **Tipo de tarea:** Mejoras · **Estimación:** 6 h · **PR/QA:** Sí
- **Descripción:** Documentar y ejecutar matriz QA.
- **Entregable esperado:** Matriz QA aprobada.
- **Criterios de aceptación:** Existe caso reproducible por cada estado.
- **Notas funcionales:** Estados normalizados.
- **Notas técnicas:** ok/pending/stale/unavailable/needs_review/not_found/not_implemented.

### TICA-051 - Validar reglas con casos reales
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Demo · **Tipo de tarea:** Mejoras · **Estimación:** 6 h · **PR/QA:** Sí
- **Descripción:** Validar selección y datos con cliente.
- **Entregable esperado:** Evidencia QA.
- **Criterios de aceptación:** Tres casos reales por modalidad core o justificación si no hay datos.
- **Notas funcionales:** Requiere disponibilidad cliente.
- **Notas técnicas:** Comparar contra operación manual.

### TICA-052 - Tests degradación y CAPTCHA
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Media
- **Tipo:** Backend · **Tipo de tarea:** Mejoras · **Estimación:** 3 h · **PR/QA:** Sí
- **Descripción:** Crear pruebas de degradación con fixtures.
- **Entregable esperado:** tests/test_degradacion.py.
- **Criterios de aceptación:** stale/unavailable/CAPTCHA simulados en verde.
- **Notas funcionales:** No resolver CAPTCHA.
- **Notas técnicas:** Simular portal caído.

### TICA-053 - Reporte cobertura QA
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Baja
- **Tipo:** Documentación · **Tipo de tarea:** Mejoras · **Estimación:** 3 h · **PR/QA:** Sí
- **Descripción:** Preparar cierre QA.
- **Entregable esperado:** Reporte de QA.
- **Criterios de aceptación:** Reporte con cobertura, casos needs_review y riesgos residuales.
- **Notas funcionales:** Soporte para entrega PM.
- **Notas técnicas:** Adjuntar evidencia.

---

## Sprint 6 - Terrestre condicional

### TICA-060 - Recibir grabación terrestre
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Baja
- **Tipo:** Documentación · **Tipo de tarea:** Mejoras · **Estimación:** 0 h · **PR/QA:** Sí
- **Descripción:** Gestionar insumo con Dokka/agencia.
- **Entregable esperado:** Grabación terrestre.
- **Criterios de aceptación:** Grabación recibida y revisada.
- **Notas funcionales:** Sin esto no iniciar F6.
- **Notas técnicas:** Confirmar ejemplo real.

### TICA-061 - Confirmar código DMS
- **Estado:** Pending · **Prioridad:** Alta · **Complejidad:** Baja
- **Tipo:** Documentación · **Tipo de tarea:** Mejoras · **Estimación:** 0 h · **PR/QA:** Sí
- **Descripción:** Confirmar código de búsqueda terrestre.
- **Entregable esperado:** Confirmación funcional.
- **Criterios de aceptación:** Nombre, formato y origen del identificador confirmados.
- **Notas funcionales:** No usar carta de porte como supuesto.
- **Notas técnicas:** Actualizar especificación.

### TICA-062 - Fixtures terrestres
- **Estado:** Pending · **Prioridad:** Media · **Complejidad:** Media
- **Tipo:** Backend · **Tipo de tarea:** Mejoras · **Estimación:** 3 h · **PR/QA:** Sí
- **Descripción:** Grabar HTML terrestre después de recibir insumos.
- **Entregable esperado:** tests/fixtures/terrestre.
- **Criterios de aceptación:** Fixtures cubren flujo confirmado.
- **Notas funcionales:** Condicional.
- **Notas técnicas:** No tocar TICA en tests.

### TICA-063 - Estrategia terrestre
- **Estado:** Pending · **Prioridad:** Media · **Complejidad:** Alta
- **Tipo:** Backend · **Tipo de tarea:** Desarrollo · **Estimación:** 12 h · **PR/QA:** Sí
- **Descripción:** Implementar terrestre.py.
- **Entregable esperado:** Estrategia terrestre.
- **Criterios de aceptación:** Implementación sigue patrón de estrategias y contrato de estados.
- **Notas funcionales:** Solo tras confirmación DMS.
- **Notas técnicas:** Actualizar docs.

### TICA-064 - Tests y validación terrestre
- **Estado:** Pending · **Prioridad:** Media · **Complejidad:** Media
- **Tipo:** Demo · **Tipo de tarea:** Mejoras · **Estimación:** 5 h · **PR/QA:** Sí
- **Descripción:** Cerrar modalidad terrestre.
- **Entregable esperado:** M6 aprobado.
- **Criterios de aceptación:** Tests verdes y validación QA con caso real.
- **Notas funcionales:** Condicional.
- **Notas técnicas:** Fixtures + caso real.
