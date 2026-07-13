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
- Fase vigente: Sprint 2 - Modalidad aerea.
- Siguiente tarea: TICA-020 - fixtures aereos sanitizados.
