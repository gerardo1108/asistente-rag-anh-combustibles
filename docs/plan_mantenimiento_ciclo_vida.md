# Plan de mantenimiento y ciclo de vida

## Estado y proposito

Propuesta para revision del equipo. El plan cubre el MVP y una posible
evolucion posterior. Su finalidad es conservar funcionamiento, trazabilidad y
calidad sin ampliar el alcance de manera descontrolada.

## Elementos bajo mantenimiento

- Interfaz web y flujo conversacional.
- Motor RAG y corpus normativo.
- Adaptador local y cliente de servicios HTTP.
- Contratos OpenAPI de Backend ANH y Ciudadania Digital.
- Panel de supervision.
- Imagenes de contenedor y dependencias.
- Pruebas, documentacion y evidencias del proyecto.

## Tipos de mantenimiento

| Tipo | Ejemplos en el proyecto | Prioridad |
| --- | --- | --- |
| Correctivo | Error de registro, estado incorrecto o servicio no disponible sin mensaje. | Alta si bloquea el flujo. |
| Adaptativo | Cambio de contrato OpenAPI, puerto, plataforma o normativa. | Segun fecha de entrada en vigor. |
| Perfectivo | Mejorar claridad, accesibilidad, latencia o recuperacion RAG. | Solo despues de medir beneficio. |
| Preventivo | Actualizar dependencias, pruebas, respaldos y documentacion. | Programado. |

## Cadencia propuesta

| Frecuencia | Actividad |
| --- | --- |
| Antes de cada demo | Salud de servicios, flujo completo, pruebas y reinicio de semillas. |
| En cada cambio | Revision de codigo, pruebas y actualizacion documental relacionada. |
| Mensual durante piloto | Revision de incidencias, calidad RAG y cambios normativos conocidos. |
| Trimestral en una evolucion real | Dependencias, seguridad, costos, capacidad y recuperacion. |
| Ante una nueva norma o contrato | Analisis de impacto, actualizacion del corpus y regresion completa. |

Estas frecuencias son una propuesta inicial y deben ajustarse al uso real.

## Gestion del corpus y del RAG

Cada fragmento normativo debe conservar fuente, seccion, fecha de incorporacion
y version. Una actualizacion del corpus requiere:

1. Confirmar la fuente oficial.
2. Registrar la norma agregada, modificada o retirada.
3. Regenerar los datos de recuperacion.
4. Ejecutar la evaluacion RAG.
5. Comparar top-1, top-3, MRR y abstencion con la linea base.
6. Aprobar el cambio solo si no aparecen regresiones criticas.

Una respuesta generativa futura debe permanecer condicionada a las fuentes
recuperadas y no controlar reglas administrativas ni estados del tramite.

## Gestion de contratos

Los archivos OpenAPI son la fuente de verdad entre equipos. Todo cambio debe:

- Identificar version y responsable.
- Explicar compatibilidad o ruptura.
- Actualizar mocks, orquestador, panel y ejemplos.
- Incluir pruebas del consumidor afectado.
- Comunicarse antes de fusionarse a la rama oficial.

Los cambios incompatibles requieren una nueva version del endpoint o una
ventana coordinada de migracion.

## Versionado y liberaciones

Se propone versionado semantico:

- `PATCH`: correccion compatible sin cambiar contratos.
- `MINOR`: funcionalidad compatible o nuevo endpoint opcional.
- `MAJOR`: cambio incompatible de contrato, datos o comportamiento.

Cada liberacion debe incluir etiqueta, notas de cambio, resultado de pruebas,
version del corpus y procedimiento de retorno. La rama `main` representa la
version aceptada; las pruebas de integracion permanecen en ramas separadas hasta
la aprobacion del equipo.

## Monitoreo

| Indicador | Umbral inicial | Accion |
| --- | ---: | --- |
| Pruebas criticas aprobadas | 100% | Bloquear liberacion si falla una. |
| Precision top-3 RAG | 80% minimo | Revisar corpus o ranking. |
| Abstencion fuera de alcance | 80% minimo | Ajustar umbral y casos de evaluacion. |
| Errores HTTP del flujo | Menos de 5% en piloto | Revisar servicio y contrato. |
| Registro completo | 95% en pruebas guiadas | Analizar paso que causa abandono. |
| Tiempo de respuesta | Definir linea base en piloto | Investigar aumentos sostenidos. |

Los umbrales operativos deben revisarse con resultados reales del piloto.

## Incidentes y soporte

1. Registrar fecha, version, ambiente, impacto y pasos para reproducir.
2. Clasificar como bloqueo total, degradacion o consulta.
3. Aplicar correccion o regresar a una version estable.
4. Verificar el flujo afectado y casos relacionados.
5. Documentar causa, solucion y accion preventiva.

Durante el MVP, el canal de soporte es el equipo del proyecto. Una operacion
real requeriria horarios, responsables y tiempos de respuesta acordados.

## Datos, respaldos y retencion

Los datos del MVP son ficticios y pueden restaurarse desde semillas. SQLite y
los archivos locales no constituyen respaldo productivo. Una evolucion real
debe definir:

- Frecuencia y cifrado de respaldos.
- Pruebas de restauracion.
- Periodo de retencion por tipo de dato.
- Eliminacion segura al concluir la finalidad.
- Acceso restringido a solicitudes y fotografias.

## Dependencias y seguridad

- Revisar versiones antes de cada liberacion relevante.
- Aplicar actualizaciones criticas de seguridad con prioridad.
- No actualizar varias dependencias importantes sin pruebas de regresion.
- Mantener imagenes base soportadas y reconstruir contenedores periodicamente.
- Retirar claves, imagenes y servicios temporales cuando termine una prueba.

## Responsabilidades propuestas

| Responsabilidad | Perfil responsable |
| --- | --- |
| Corpus, evaluacion RAG y calidad de respuestas | Responsable de RAG. |
| Orquestador y adaptador de integracion | Responsable del asistente. |
| Backend ANH y Ciudadania Digital simulados | Responsable de servicios externos. |
| Interfaz y panel de supervision | Responsable de experiencia y supervision. |
| Liberacion y evidencias | Equipo, con una persona designada por version. |

Los nombres y responsables finales deben confirmarse en la reunion.

## Fin de vida

Una version se retira cuando deja de ser compatible con la normativa, los
contratos o la plataforma, o cuando otra version estable la reemplaza. Antes de
retirarla se conservan evidencias academicas, se eliminan recursos temporales y
se documenta si los datos deben migrarse, conservarse o destruirse.

## Decisiones pendientes de la reunion

- Confirmar responsables por componente.
- Acordar versionado y proceso de aprobacion.
- Definir duracion y participantes del piloto.
- Establecer quien monitorea y detiene recursos en la nube.
- Decidir si estos planes forman parte del repositorio oficial o solo del
  documento academico final.

