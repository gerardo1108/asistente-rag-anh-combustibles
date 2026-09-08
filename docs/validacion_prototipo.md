# Validacion tecnica del prototipo

## Objetivo

Este documento resume la validacion inicial del prototipo de asistente RAG para
orientacion normativa y registro simulado de solicitudes de combustible liquido
fuera de tanque ante la ANH.

La validacion busca demostrar cuatro aspectos observados como relevantes para el
proyecto:

1. El alcance esta acotado a un tramite especifico.
2. Las respuestas normativas son trazables a fuentes del corpus.
3. El flujo guiado reduce errores de llenado antes de registrar una solicitud.
4. El sistema evita afirmar integraciones reales no disponibles en el prototipo.

## Alcance Validado

El prototipo validado cubre:

- Consulta normativa sobre requisitos, fotografia, estados, Ciudadania Digital,
  limites simulados, correccion de observaciones, seguimiento, vigencia,
  canales oficiales y responsabilidad normativa.
- Registro conversacional guiado de una solicitud simulada.
- Validacion de CI contra una base local de Ciudadania Digital simulada.
- Validacion de zona, combustible, volumen y fotografia.
- Creacion de solicitud en estado `pendiente`.
- Consulta y actualizacion de estado desde un panel evaluador simulado.
- Comparacion entre motor `LexicalRAG` y motor `HybridRAG`.

No cubre todavia:

- Integracion real con API oficial de Ciudadania Digital.
- Integracion real con sistemas internos de la ANH.
- Persistencia productiva en base de datos.
- Autenticacion de usuarios reales.
- Emision de decisiones administrativas oficiales.

## Metricas RAG

La evaluacion RAG se ejecuta con:

```bash
python eval/evaluate_rag.py --mode both
```

El set de evaluacion contiene 20 consultas clasificadas por categoria. Cada caso
define una consulta, fuente esperada y fragmento esperado del corpus. Tambien
incluye casos fuera de alcance para validar abstencion.

| Motor | Casos | Recuperacion | Precision general | Precision top-1 | Precision top-3 | Abstencion | MRR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `LexicalRAG` | 20 | 18 | 100% | 83% | 100% | 100% | 0.92 |
| `HybridRAG` | 20 | 18 | 100% | 89% | 100% | 100% | 0.94 |

Interpretacion:

- `top-1` mide si el fragmento correcto queda en la primera posicion.
- `top-3` mide si el fragmento correcto aparece entre las tres primeras
  evidencias recuperadas.
- `Precision general` combina recuperacion correcta y abstencion correcta.
- `Abstencion` mide si el asistente evita responder cuando la consulta queda
  fuera del alcance del corpus.
- `MRR` mide que tan arriba queda posicionada la evidencia correcta.

El umbral minimo definido para esta etapa es 80% de precision top-3. Ambos
motores cumplen el umbral con 100%.

## Casos de Evaluacion RAG

| ID | Categoria | Evidencia esperada |
| --- | --- | --- |
| `registro-requisitos-bidon` | requisitos | `reglamento-anh-registro` |
| `registro-foto-carnet` | documentacion | `reglamento-anh-fotografia` |
| `ciudadania-digital` | identidad | `agetic-ciudadania-digital` |
| `estado-rechazada` | seguimiento | `reglamento-anh-estados` |
| `limite-fronterizo` | validacion | `limites-volumen-prototipo` |
| `formulario-electronico` | tramite | `ds5400-formulario-electronico` |
| `envases-aptos` | tramite | `ds5400-formulario-electronico` |
| `destino-uso` | requisitos | `reglamento-anh-registro` |
| `estado-aprobada` | seguimiento | `reglamento-anh-estados` |
| `responsabilidad-normativa` | seguridad | `alcance-responsabilidad` |
| `limite-nacional` | validacion | `limites-volumen-prototipo` |
| `api-oficial-simulada` | integracion | `agetic-ciudadania-digital` |
| `corregir-observaciones` | seguimiento | `reglamento-anh-correccion-observaciones` |
| `seguimiento-codigo-ci` | seguimiento | `reglamento-anh-seguimiento-codigo` |
| `coherencia-datos` | validacion | `reglamento-anh-declaracion-responsable` |
| `dudas-canales-oficiales` | seguridad | `alcance-canales-oficiales` |
| `vigencia-solicitud-real` | alcance | `alcance-vigencia-prototipo` |
| `errores-llenado` | validacion | `reglamento-anh-declaracion-responsable` |
| `fuera-alcance-pasaporte` | fuera_alcance | Abstencion esperada |
| `fuera-alcance-multa-transito` | fuera_alcance | Abstencion esperada |

## Pruebas Funcionales del Flujo

Las pruebas funcionales se ejecutan con:

```bash
python -m unittest discover -s tests
```

Resultado actual:

```text
Ran 11 tests
OK
```

Las pruebas usan un archivo temporal para solicitudes, por lo que no contaminan
los datos locales de la demostracion.

## Matriz de Casos Funcionales

| Caso | Entrada o condicion | Resultado esperado | Estado |
| --- | --- | --- | --- |
| Registro exitoso | CI valido, zona nacional, gasolina, 20 litros, foto valida y confirmacion | Crea solicitud en estado `pendiente` | OK |
| CI inexistente | CI `0000000` | No avanza del paso de CI ni crea solicitud | OK |
| Zona invalida | Zona `urbana` | Mantiene el flujo en `ask_zone` | OK |
| Combustible invalido | Combustible `kerosene` | Mantiene el flujo en `ask_fuel` | OK |
| Volumen no numerico | Volumen `veinte` | Mantiene el flujo en `ask_volume` | OK |
| Volumen fronterizo excedido | Zona fronteriza y 80 litros | Rechaza antes de registrar por superar 50 litros | OK |
| Volumen nacional excedido | Zona nacional y 150 litros | Rechaza antes de registrar por superar 120 litros | OK |
| Fotografia no valida | Texto distinto a `foto ok` | Mantiene el flujo en `ask_photo` | OK |
| Cancelacion | Usuario responde `no` en confirmacion | No crea solicitud y vuelve a `idle` | OK |
| Consulta normativa | Pregunta sobre requisitos | Responde con fuentes sin iniciar registro | OK |
| Consulta fuera de alcance | Pregunta sobre renovacion de pasaporte | Responde con abstencion y no crea solicitud | OK |

## Trazabilidad y Control de Alucinaciones

El prototipo reduce el riesgo de respuestas sin sustento mediante estas reglas:

- Las respuestas normativas se construyen a partir de fragmentos recuperados del
  corpus `data/corpus_normativo.json`.
- Cada respuesta muestra fuentes y secciones recuperadas.
- Si no existe evidencia suficiente, el motor devuelve una respuesta de
  abstencion.
- El texto de descargo aclara que la respuesta es orientativa y no reemplaza una
  decision oficial de la ANH.
- La integracion con Ciudadania Digital se declara explicitamente como simulada.

## Relacion con Observaciones del Docente

| Observacion | Respuesta actual del prototipo |
| --- | --- |
| Acotar el alcance | Se limita al registro de consumo de combustible liquido fuera de tanque ante la ANH. |
| Definir fuentes especificas | El corpus curado incluye Decreto Supremo N. 5400, reglamento ANH, lineamientos AGETIC y reglas de negocio del prototipo. |
| Fortalecer evaluacion | Se agregaron 20 casos RAG con top-1, top-3, MRR y abstencion, mas 10 pruebas funcionales del flujo. |
| Cuidar alucinaciones | El asistente responde con fuentes, abstencion y descargo de responsabilidad. |
| Medir reduccion de errores | Las pruebas funcionales validan que CI, zona, combustible, volumen y fotografia se controlan antes de registrar. |

## Riesgos Pendientes

- El corpus normativo sigue siendo curado manualmente, aunque ya cubre mas
  escenarios del tramite.
- `HybridRAG` usa TF-IDF local, no embeddings semanticos reales.
- El backend institucional es simulado.
- La sesion conversacional es global; no separa usuarios concurrentes.
- El panel evaluador no tiene autenticacion.
- Las metricas de satisfaccion de usuario aun no se han levantado con usuarios
  reales o companeros de prueba.

## Proximos Pasos Recomendados

1. Ampliar el corpus con mas fragmentos normativos y administrativos.
2. Incorporar embeddings reales con ChromaDB o FAISS.
3. Agregar pruebas de interfaz o capturas de evidencia para la defensa.
4. Separar sesiones por usuario si el prototipo crece.
5. Crear una encuesta breve de satisfaccion para medir claridad, utilidad y
   confianza percibida.
