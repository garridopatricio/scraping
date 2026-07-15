# Documentacion del proyecto

Esta carpeta concentra los documentos vivos y cierres del proyecto `scrapping-tica`.

## Indice

- [Backlog de desarrollo](BACKLOG-DESARROLLO.md)
- [Proceso de consulta TICA paso a paso](PROCESO-CONSULTA-TICA-PASO-A-PASO.md)
- [Tareas del proyecto Dokka Scrapping](TAREAS-DOKKA-SCRAPPING.md)
- [Cierre Sprint 0 - PoC TICA](SPRINT-0-CIERRE.md)
- [Seguimiento Sprint 1 - Infra base](SPRINT-1-AVANCES.md)
- [Revision del contrato API - TICA-018](SPRINT-1-CONTRATO-API.md)
- [Guia de uso y ejecucion de FastAPI](GUIA-FASTAPI.md)
- [Seguimiento Sprint 2 - Modalidad aerea](SPRINT-2-AVANCES.md)
- [Seguimiento Sprint 3 - Modalidad maritima](SPRINT-3-AVANCES.md)

## Guia FastAPI y contrato API

Estos documentos son complementarios, pero tienen objetivos diferentes:

| Documento | Proposito | Publico principal |
|---|---|---|
| [Guia de FastAPI](GUIA-FASTAPI.md) | Explica como instalar, ejecutar, probar y entender el servicio, incluyendo Uvicorn, Swagger, PowerShell y la relacion entre API, orquestador y scraper. | Personas que desarrollan, mantienen o ejecutan el proyecto. |
| [Contrato API](SPRINT-1-CONTRATO-API.md) | Define el acuerdo de integracion: request, response, campos, tipos, estados y codigos HTTP. | Equipos o sistemas consumidores, como RAGA Orders. |

En resumen:

- Consultar la **guia de FastAPI** para saber como levantar y operar el servicio.
- Consultar el **contrato API** para saber que enviar y que respuesta esperar.
- La guia cambia cuando cambia la instalacion, ejecucion u operacion.
- El contrato cambia cuando cambian campos, tipos, estados o respuestas que afectan a los consumidores.

Los documentos generales de planificacion se mantienen en esta carpeta. Las evidencias y salidas locales de la PoC permanecen fuera del repositorio del microservicio.

## Estado actual

- Sprint 1: completado, 9 de 9 tareas; hito M1 aprobado.
- Sprint 2: completado, 7 de 7 tareas; hito M2 aprobado con limitacion documentada.
- TICA-020 se cierra con excepcion aceptada: no se dispuso de casos reales sin arribo ni multi-ING; las ramas quedan cubiertas estructuralmente hasta poder revalidarlas.
- TICA-026 completada: QA confirmado con los casos aereos disponibles.
- Sprint 3 completado: TICA-030 a TICA-036 terminadas; M3 aprobado.
- Siguiente fase: Sprint 4 - Integracion RAGA Orders.
- La cedula maritima es configuracion interna; anticipados y conocimientos con varias lineas estan implementados.
- Request vigente: `manifiestos` (1-100), `fecha_fin` obligatoria y `fecha_inicio` opcional.
- Si se omite `fecha_inicio`, el campo queda vacio en TICA; si se envia, la ventana inclusiva admite hasta 15 dias.
- Response vigente: objeto indexado directamente por manifiesto, sin secciones `regla` ni `resultados`.
- El procesamiento es secuencial por manifiesto; aereo y maritimo estan migrados.

`BACKLOG-DESARROLLO.md`, `TAREAS-DOKKA-SCRAPPING.md` y el documento del proceso manual son fuentes originales de planificacion y negocio. El contrato implementado y sus cambios posteriores se consultan en `SPRINT-1-CONTRATO-API.md` y `SPRINT-1-AVANCES.md`.
