# Plan de posible despliegue real

## Estado y alcance

Este plan describe una evolucion posible posterior al MVP. No afirma que el
prototipo actual este listo para produccion ni compromete al equipo a ejecutar
el despliegue. Su objetivo es demostrar viabilidad y establecer las condiciones
que tendrian que cumplirse antes de operar con usuarios y datos reales.

## Objetivo operativo

Ofrecer un asistente disponible por Internet que oriente sobre el tramite,
registre solicitudes en un backend institucional, permita su supervision y
muestre estados sin exponer informacion personal ni depender de almacenamiento
temporal.

## Diferencias entre MVP y produccion

| Dimension | MVP actual | Requisito para produccion |
| --- | --- | --- |
| Identidad | Ciudadania Digital simulada. | Integracion autorizada, autenticacion y consentimiento. |
| Backend ANH | Mock con SQLite. | Servicio institucional y base persistente. |
| Fotografias | Evidencia textual simulada. | Carga segura, cifrado, retencion y revision autorizada. |
| RAG | Corpus local curado. | Gobierno documental, actualizacion y trazabilidad de versiones. |
| Usuarios | Pruebas controladas. | Sesiones independientes, control de acceso y auditoria. |
| Disponibilidad | Ejecucion local o temporal. | Monitoreo, objetivos de servicio y recuperacion. |
| Seguridad | Datos ficticios y clave de prueba. | IAM, secretos, minimo privilegio y evaluacion de riesgos. |

## Arquitectura objetivo de referencia

```text
Ciudadano
   |
   v
Aplicacion web publica
   |
   +-- Orquestador y RAG
   |      `-- Repositorio normativo versionado
   |
   +-- Servicio de identidad autorizado
   |
   `-- Backend ANH
          |-- Base de datos persistente
          `-- Almacenamiento seguro de adjuntos

Panel de supervision privado
   `-- Backend ANH con permisos diferenciados
```

La arquitectura definitiva dependeria de los servicios autorizados por ANH y
AGETIC. Los contratos del MVP sirven como referencia, no como garantia de
compatibilidad con sistemas gubernamentales reales.

## Fases propuestas

### Fase 1. Estabilizacion del prototipo

- Congelar los contratos OpenAPI.
- Completar pruebas de integracion y manejo de errores.
- Ejecutar el piloto con datos ficticios.
- Confirmar metricas Lean y criterios de continuidad.

### Fase 2. Preparacion preproductiva

- Sustituir SQLite por una base persistente.
- Separar acceso publico y supervision privada.
- Implementar autenticacion, autorizacion y gestion de secretos.
- Crear ambientes de desarrollo, pruebas y preproduccion.
- Automatizar pruebas, construccion y despliegue.

### Fase 3. Validacion institucional

- Revisar privacidad, seguridad y tratamiento de datos personales.
- Acordar contratos reales con ANH y AGETIC.
- Ejecutar pruebas de carga, accesibilidad y recuperacion.
- Obtener autorizaciones tecnicas y administrativas.

### Fase 4. Liberacion controlada

- Publicar una version para un grupo limitado.
- Monitorear errores, tiempos de respuesta y calidad del RAG.
- Activar soporte y procedimiento de incidentes.
- Ampliar usuarios solo si se cumplen los umbrales acordados.

## Estrategia de versiones y ambientes

| Ambiente | Rama o version | Aprobacion requerida |
| --- | --- | --- |
| Desarrollo | Ramas de funcionalidad e integracion. | Revision tecnica. |
| Pruebas | Version candidata etiquetada. | Pruebas automatizadas e integracion. |
| Preproduccion | Misma imagen candidata a produccion. | Seguridad, negocio y aceptacion. |
| Produccion | Version inmutable aprobada. | Responsable de liberacion. |

Cada despliegue debe registrar version de aplicacion, version del corpus,
contratos OpenAPI, fecha, responsable y resultado de verificaciones.

## Controles minimos

- Cifrado en transito y en reposo.
- Identidades de servicio con minimo privilegio.
- Secretos fuera del codigo y de Git.
- Registros de auditoria sin datos personales innecesarios.
- Politicas de retencion y eliminacion de solicitudes y adjuntos.
- Limites de solicitudes y proteccion contra abuso.
- Revision humana para decisiones administrativas.
- Mensajes que indiquen que el asistente no sustituye una resolucion oficial.

## Observabilidad

El entorno debe medir disponibilidad, tasa de errores, latencia, fallos por
servicio, consumo, solicitudes incompletas y calidad del RAG. Las alertas deben
identificar quien atiende el incidente y cuando se activa el modo de
contingencia.

## Estrategia de retorno

Una version no se libera si fallan pruebas criticas, contratos o controles de
seguridad. Si una revision desplegada produce errores, se dirige el trafico a
la version estable anterior. Las migraciones de datos deben contar con respaldo
y un procedimiento de restauracion probado.

## Estimacion inicial

El equipo debe estimar costos despues de definir volumen de usuarios,
almacenamiento, retencion, region y servicios administrados. El credito temporal
de una cuenta academica no constituye un modelo financiero de produccion.

## Criterio de decision

El proyecto avanza hacia produccion solamente si el piloto demuestra utilidad,
la calidad del RAG cumple sus umbrales, existen acuerdos institucionales y el
equipo puede operar seguridad, soporte y mantenimiento. En caso contrario, el
resultado se conserva como MVP validado y propuesta de trabajo futuro.

