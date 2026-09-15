# Plan Lean del MVP y criterios de decision

## Proposito

Este documento aterriza la observacion recibida en la Entrega 2: concretar como
se aplicara Lean al MVP, definir un referente de comparacion y establecer reglas
para decidir a partir de metricas.

El MVP se evalua como asistente de orientacion y registro simulado para el
tramite de consumo de combustible liquido fuera de tanque ante la ANH. Su valor
no se mide por tener integraciones productivas, sino por demostrar que el flujo
reduce errores de llenado, responde con evidencia normativa y permite seguimiento
comprensible.

## Hipotesis Lean

| Hipotesis | Senal esperada | Como se prueba en el MVP |
| --- | --- | --- |
| Un asistente guiado reduce errores antes de crear la solicitud. | Menos pasos corregidos y menos solicitudes incompletas frente a un formulario libre. | Pruebas funcionales de CI, zona, combustible, volumen, destino y fotografia simulada. |
| Un RAG trazable reduce respuestas sin sustento. | Las respuestas relevantes muestran fuentes y las consultas fuera de alcance reciben abstencion. | Evaluacion RAG con top-1, top-3, MRR y abstencion. |
| El seguimiento por codigo y CI mejora la claridad posterior al registro. | El usuario puede consultar estado sin repetir todo el tramite. | Consulta de estado desde bloque de seguimiento y desde chat. |
| Una simulacion controlada de fotografia es suficiente para el prototipo academico. | El flujo valida la presencia de evidencia sin prometer biometria real. | Campo de evidencia fotografica simulada y visualizacion en panel evaluador. |

## Referente de comparacion

El referente de comparacion del MVP sera un flujo base manual:

1. El usuario lee requisitos normativos o instrucciones generales.
2. Completa la solicitud sin validaciones conversacionales paso a paso.
3. Detecta errores solo al final o cuando una persona revisa el tramite.
4. Consulta el estado por una ruta separada, sin soporte conversacional.

El prototipo se compara contra ese referente en tres dimensiones:

| Dimension | Flujo base manual | MVP propuesto |
| --- | --- | --- |
| Prevencion de errores | El error se detecta tarde. | El asistente detiene entradas invalidas antes de registrar. |
| Trazabilidad normativa | La fuente puede quedar separada de la respuesta. | Cada respuesta normativa muestra fuentes recuperadas. |
| Seguimiento | El usuario debe conocer la ruta exacta de consulta. | El estado se consulta por codigo y CI desde el chat o el bloque de seguimiento. |

## Metricas del MVP

| Metrica | Umbral minimo para mantener enfoque | Meta deseada para la siguiente entrega | Fuente de medicion |
| --- | ---: | ---: | --- |
| Precision top-3 del RAG | 80% | 90% o mas | `python3 eval/evaluate_rag.py --mode both` |
| Abstencion fuera de alcance | 80% | 100% | Casos fuera de alcance del set RAG |
| Pruebas funcionales del flujo | 90% OK | 100% OK | `python3 -m unittest discover -s tests` |
| Tasa de bloqueo de errores antes del registro | 80% de casos invalidos bloqueados | 100% en casos definidos | Tests de CI, zona, combustible, volumen y fotografia |
| Claridad percibida en piloto | 4/5 | 4.5/5 | Encuesta corta a companeros o usuarios de prueba |
| Tiempo de registro guiado | Igual o menor al flujo manual observado | Reducir al menos 20% | Cronometraje de prueba con tareas equivalentes |

## Reglas de decision

| Resultado medido | Decision |
| --- | --- |
| Top-3 RAG menor a 80% | No ampliar funcionalidades; primero mejorar corpus, fragmentacion o ranking. |
| Abstencion menor a 80% | Ajustar umbral de similitud y casos fuera de alcance antes de demo final. |
| Una prueba funcional critica falla | Corregir el flujo antes de grabar video o presentar evidencias. |
| Usuarios no entienden que la fotografia es simulada | Reforzar textos de UI y documentacion para no prometer biometria real. |
| Claridad percibida menor a 4/5 | Revisar lenguaje de respuestas, resumen final y mensajes de validacion. |
| Tiempo de registro mayor al flujo manual | Reducir pasos redundantes o mejorar prompts del asistente. |
| Todas las metricas cumplen umbral | Congelar alcance del MVP y dedicar esfuerzo a defensa, video y documentacion. |

## Aplicacion al estado actual

Al 15 de septiembre de 2026, el MVP cumple los umbrales tecnicos internos:

- `HybridRAG`: precision general 100%, top-1 89%, top-3 100%, abstencion 100% y MRR 0.94.
- `LexicalRAG`: precision general 100%, top-1 83%, top-3 100%, abstencion 100% y MRR 0.92.
- Pruebas funcionales: 15 pruebas ejecutadas, 15 OK.
- Trello: 21 tarjetas en `Hecho`; quedan en backlog piloto con usuarios reales, video demostrativo y carga real de fotografias.

La decision recomendada es congelar nuevas funcionalidades del prototipo y
concentrar el siguiente avance en evidencia de validacion: capturas, video,
piloto breve y redaccion final del capitulo de resultados.

## Texto sugerido para el informe

El MVP se desarrollo siguiendo un ciclo Lean de construir, medir y aprender. En
la etapa de construccion se implemento un flujo minimo que permite consultar
normativa, registrar una solicitud simulada, validar datos criticos antes del
envio y consultar el estado por codigo y CI. En la etapa de medicion se definio
un referente de comparacion equivalente a un flujo manual sin asistencia
conversacional, donde los errores se detectan al final del tramite o durante la
revision. Frente a este referente, el MVP se evalua por su capacidad para
prevenir errores de llenado, responder con fuentes recuperadas y facilitar el
seguimiento posterior.

Las metricas principales son precision top-3 del RAG, abstencion ante consultas
fuera de alcance, pruebas funcionales del flujo, bloqueo de entradas invalidas,
claridad percibida y tiempo de registro guiado. Las reglas de decision establecen
que, si la precision top-3 baja de 80% o alguna prueba critica falla, no se
agregaran nuevas funcionalidades hasta corregir la base del prototipo. Si las
metricas tecnicas cumplen los umbrales, se congela el alcance y se prioriza la
validacion con usuarios y la preparacion de la defensa.

En el estado actual, el prototipo cumple los umbrales tecnicos definidos: el
motor hibrido alcanza 100% en top-3 y abstencion, y las 15 pruebas funcionales
del flujo conversacional se ejecutan correctamente. Por ello, la decision del
equipo es mantener fuera de alcance la biometria real y documentar la fotografia
como una simulacion controlada sin reconocimiento facial, suficiente para validar
el flujo academico sin introducir riesgos tecnicos o legales innecesarios.
