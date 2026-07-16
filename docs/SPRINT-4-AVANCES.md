# Sprint 4 - Integracion DOKKA-TICA

## Estado

| Dato | Resultado |
|---|---|
| Estado | Completado localmente |
| Hito | M4 - Integracion RAGA |
| Tareas | TICA-040 a TICA-042 completadas |
| Base de datos | Sin tablas, migraciones ni columnas nuevas |
| QA | 8 SD sincronizados con TICA real |

## Implementado

- Scraper integrado dentro de DOKKA como proceso FastAPI separado.
- Cliente Laravel, resolver de guia hija/HBL, mapper, Job y Command.
- Scheduler horario y cola serial `tica-sync`, independientes de Porth.
- Inicio automatico local al entrar en Embarques y refresco Livewire.
- Persistencia limitada a `dua_number`, `dua_released_date` y `notes`.
- Reintento horario hasta 72 consultas y detencion al completar.

## Evidencia QA

Los 8 SD locales con guia hija finalizaron `complete`. Se reemplazaron los DUAs ficticios
por datos TICA y se verifico directamente PostgreSQL. El detalle se encuentra en
`INTEGRACION-SCRAPPING-DOKKA-TICA.md`.

## Pendiente operativo

- Definir URL y supervision de FastAPI en QA/produccion.
- Mantener un unico worker para `tica-sync`.
- Decidir en una fase futura si produccion filtra SD por estado.
- Crear rama, commit y despliegue solo cuando sean solicitados.
