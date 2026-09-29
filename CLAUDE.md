# CLAUDE.md — Epic 1, servicio RAG e interfaz de chat

Instrucciones para el asistente de código. Leer antes de trabajar en este repositorio.

Este documento cubre el **Epic 1** (los mocks del Backend ANH y de Ciudadanía
Digital), el **servicio RAG** (`src/rag`, puerto 8003), el **servicio de
validación de imágenes** (`src/validacion_imagenes`, puerto 8004) y la
**interfaz de chat** (`src/chat_web`, puerto 8080). El orquestador y el
panel del evaluador quedan fuera de alcance aquí.

---

## Qué se construye

Los mocks del **Backend ANH** y **Ciudadanía Digital**, más el **servicio
RAG** y la **interfaz de chat**, sostienen el prototipo de un **asistente
conversacional basado en LLM + RAG** para el trámite de **registro de
consumo de combustibles líquidos fuera de tanque** ante la ANH (Agencia
Nacional de Hidrocarburos, Bolivia).

Es un trabajo académico de maestría (UNIR). **Nunca se integrará con los
sistemas reales de la ANH ni de AGETIC.** Los mocks no son implementaciones a
medias: son componentes simulados de forma deliberada y permanente. El
servicio RAG y la interfaz de chat son distintos en naturaleza: no simulan
nada externo, son los componentes reales que resuelven el trámite.

| Servicio | Puerto | Qué es |
|---|---|---|
| **Backend ANH** (mock) | 8001 | Sistema de trámites de la entidad, simulado |
| **Ciudadanía Digital** (mock) | 8002 | Servicio de identidad de AGETIC, simulado |
| **RAG** (real) | 8003 | Motor de recuperación aumentada sobre el corpus normativo |
| **Validación de imágenes** (real) | 8004 | Verifica que la foto del ciudadano muestre rostro y cédula sin sobreposiciones |
| **Chat** (real) | 8080 | Interfaz web (HTML/CSS/JS vanilla) que consume los cuatro anteriores |

Los cuatro servicios backend se levantan con `docker compose up`. La interfaz
de chat corre local, aparte (ver "Interfaz de chat" más abajo). Todo local,
sin hosting.

---

## Contratos — fuente de verdad

Seis especificaciones OpenAPI 3.0.3 en `/contratos`. **Si el código no
coincide con la spec, se corrige el código, no la spec.**

### `openapi-integracion.yaml` → Backend ANH (8001)

El **contrato estándar**: lo que el asistente consume. Pensado para que
cualquier entidad pública lo adopte.

- `POST /v1/solicitudes` — registrar una solicitud, devuelve el código de trámite
- `GET /v1/solicitudes/{codigo}/estado` — consultar seguimiento

### `openapi-supervision-anh.yaml` → Backend ANH (8001)

Operaciones **internas de la ANH**, para la aplicación de supervisión del
evaluador. No son parte del estándar: son el caso de uso particular de esta
entidad.

- `GET /v1/solicitudes` — listar (resumen, con filtro por estado y paginación)
- `GET /v1/solicitudes/{codigo}` — detalle completo, con datos y adjuntos
- `PATCH /v1/solicitudes/{codigo}/estado` — resolver: aprobar o rechazar

### `openapi-ciudadania-digital.yaml` → Ciudadanía Digital (8002)

- `POST /v1/verificacion-ciudadania` — datos del titular registrado

### `openapi-rag.yaml` → Servicio RAG (8003)

Consumido por la interfaz de chat y, fuera de este repositorio, por el
orquestador. Recibe una pregunta en lenguaje natural y devuelve una
respuesta fundamentada en el corpus normativo, con las fuentes citadas. Se
abstiene explícitamente si no encuentra información relevante, en lugar de
inventar contenido.

- `POST /v1/consultas-rag` — consulta al motor de recuperación aumentada

### `openapi-validacion-imagenes.yaml` → Servicio de validación de imágenes (8004)

Consumido por la interfaz de chat, antes de enviar la solicitud al Backend
ANH. Recibe la foto del ciudadano y devuelve un veredicto de si muestra, con
claridad y sin sobreposiciones, un rostro humano y una cédula de identidad.
Es un pre-filtro automático de presencia y oclusión: no evalúa legibilidad
fina, vigencia del documento, ni que el rostro corresponda a la persona
registrada en Ciudadanía Digital — eso sigue siendo responsabilidad del
evaluador humano. Si la imagen no es interpretable (borrosa, oscura, no es
una foto de una persona), responde igual con `200` y `veredicto: INVALIDA`,
en vez de un error: la abstención es un resultado válido de la evaluación,
distinto de una falla del servicio (`500`, cuando el proveedor de visión no
respondió correctamente tras los reintentos).

- `POST /v1/validaciones-imagen` — evalúa una fotografía

### `openapi-utilidades-prototipo.yaml` → ambos mocks (8001 y 8002)

Operaciones de instrumentación del prototipo, no del dominio del trámite.
Ningún sistema real las expondría; existen porque estos servicios son
simulados y necesitan operarse durante el desarrollo y la demostración.

- `GET /health` — verifica que el servicio responde; sin credencial
- `POST /reiniciar` — descarta los datos acumulados y recarga las semillas;
  sin credencial; solo responde si `PERMITIR_REINICIO` está activa

**Las specs de integración y supervisión las implementa el mismo servicio**,
sobre los mismos datos: el evaluador revisa las solicitudes que ingresaron por
el contrato estándar. La separación en archivos es documental, para que la
frontera entre lo estándar y lo particular quede visible. No separar en
procesos.

**Cambios a estos contratos son cambios públicos**: los consume la interfaz
de chat y, fuera de este repositorio, el orquestador. Un cambio a un contrato
requiere avisar a quien consuma ese servicio; un cambio a la implementación
interna (que no toque la spec), no.

---

## Decisiones cerradas

Discutidas y acordadas. **No revertir sin motivo explícito**, aunque en
abstracto parezcan mejorables.

**Sobre fijo, contenido opaco.** El cuerpo del registro tiene una estructura
idéntica para cualquier trámite (`tramite`, `version_formulario`, `solicitante`,
`datos`, `adjuntos`, `declaracion_jurada`, `canal_origen`). Solo `datos` cambia
entre trámites, y el servicio lo transporta sin interpretarlo.

**`datos` es vertical.** Arreglo de `{campo, indice?, valor}`, no un objeto cuyas
claves cambian. Así la estructura del mensaje no varía entre entidades y puede
describirse por completo en la spec. El `indice` opcional agrupa repeticiones
para formularios que declaran un grupo de campos más de una vez.

**Solo se transmite lo que varía.** La etiqueta legible, el tipo de dato y demás
características de cada campo NO viajan en el mensaje: el asistente las conoce
por sus prompts y la entidad por su propio formulario. Se descartaron
explícitamente los atributos `etiqueta`, `tipo` y `origen`.

**El nombre va en tres campos**, no concatenado: `nombres`, `primer_apellido`,
`segundo_apellido`. Concatenar pierde información irrecuperable, y es como lo
entrega Ciudadanía Digital.

**La validación normativa vive en el asistente, no en el servicio.** El servicio
valida estructura. Los límites de volumen y demás reglas del reglamento los
verifica el orquestador antes de invocarlo.

**No hay webhooks ni notificación de eventos.** El seguimiento es por consulta.
Se descartó el push para no exigir a la entidad llamadas salientes hacia un
sistema externo.

**No se generaliza la ingesta del corpus ni la definición del formulario.** Eso
es configuración particular de cada implementación (chunking, prompts), no parte
del contrato. Lo generalizable es la conexión.

**Dos claves de API distintas.** `AsistenteApiKey` habilita el contrato estándar;
`SupervisionApiKey` habilita las operaciones internas. El asistente no puede
resolver trámites; la supervisión no registra solicitudes. Ambas se declaran pero
el mock acepta cualquier valor.

**Sin verificación de titularidad en la consulta de estado.** El código de
trámite es la única credencial. Limitación explícita del prototipo, documentada
en la spec.

**El flujo OIDC de Ciudadanía Digital está simulado.** En producción los datos
del titular se obtienen tras autenticación y consentimiento. El mock consulta por
número de documento. Limitación explícita, documentada en la spec.

**CORS abierto (`allow_origins=["*"]`) en los cuatro servicios.** La interfaz
de chat llama a los cuatro directo desde el navegador (`fetch`), no desde
Python servidor-a-servidor, así que quedan sujetos a CORS. Un allowlist de
orígenes sería una cosa más para mantener sincronizada sin aportar
seguridad real: es un prototipo local, sin credenciales reales (las API
keys son valores mock que el servicio acepta igual). No usar
`allow_credentials=True` junto con `allow_origins=["*"]`: Starlette lo
rechaza, y tampoco hace falta — la auth es el header `X-API-Key`, no cookies.

---

## Persistencia y semillas

Persistencia real desde el inicio, sin versión intermedia en memoria.

- Persistencia en **SQLite**: un archivo, sin servidor, sin dependencias nuevas.
- Datos iniciales desde un **archivo JSON de semillas** versionado en el repo.
- Imágenes como **archivos sueltos** en `semillas/imagenes/`, referenciadas por
  nombre desde el JSON. El mock las lee al arrancar y las codifica en base64.
  No incrustar base64 en el JSON: lo vuelve ilegible en Git.
- Redimensionar las fotos antes de usarlas como semilla (~800 px de ancho).
- **Endpoint de reinicio** (`POST /reiniciar`, ver
  `openapi-utilidades-prototipo.yaml`) que restaura el estado inicial, para
  poder repetir tomas al grabar el video.

### Para no perder velocidad al arrancar

Empezar con 2 o 3 casos mínimos —un trámite registrado, uno aprobado, uno
rechazado— con fotos *placeholder* si hace falta, para no bloquear el resto
del trabajo mientras se preparan las semillas definitivas. Sumar el resto de
los casos y las fotos reales en paralelo, sin que eso retrase la disponibilidad
básica del servicio.

Casos de semilla objetivo: trámite aprobado, rechazado con motivo legible,
pendiente de evaluación, persona sin Ciudadanía Digital, persona que requiere
revalidación.

### Implicación de diseño

Igual mantener la persistencia **detrás de una abstracción** (`almacen.py` o
equivalente), separada de la lógica de las operaciones. No porque vaya a cambiar
de motor, sino porque hace el código más simple de probar y de razonar.

---

## Servicio RAG

`src/rag`, puerto 8003. Motor de recuperación aumentada (RAG) sobre el corpus
normativo (`.md` en `src/rag/corpus`, chunked por artículo e indexado en
Chroma). A diferencia de los mocks, no simula un sistema externo: es el
componente real que resuelve las preguntas del ciudadano contra la normativa,
con abstención explícita cuando no encuentra información relevante en lugar
de inventar contenido.

### Levantar el servicio

**Local**, para iterar rápido:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-rag.txt

cd src
python -m rag.ingest          # prerequisito, ver abajo
uvicorn rag.main:app --reload --port 8003
```

**Docker:**

```bash
docker compose up rag
```

`src/rag/Dockerfile` construye el índice durante el build de la imagen, así
el contenedor arranca sin reindexar.

### Prerequisito: construir el índice

`ingest.py` **no corre en cada arranque** de `main.py` — a diferencia de los
mocks, que recargan sus semillas SQLite al iniciar. Reconstruir el índice
(cuando cambia el corpus) es un paso manual:

```bash
cd src && python -m rag.ingest
```

Si el índice no existe, `main.py` falla al arrancar con un mensaje explícito
pidiendo correr `ingest.py` primero, en lugar de arrancar vacío o reindexar
solo.

### Variables de entorno

Requeridas según qué proveedores estén activos en `LLM_PROVEEDORES` (ver
abajo; con el default `groq,gemini` se necesitan ambas):

| Variable | Qué controla |
|---|---|
| `GOOGLE_API_KEY` | Clave de Gemini API. Requerida si `gemini` está en `LLM_PROVEEDORES`. Se consigue gratis en https://aistudio.google.com/apikey. |
| `GROQ_API_KEY` | Clave de Groq API. Requerida si `groq` está en `LLM_PROVEEDORES`. Se consigue gratis en https://console.groq.com/keys. |

Ninguna clave va hardcodeada: van en un `.env` en la raíz del repo (gitignored).

Opcionales, con default razonable:

| Variable | Default | Qué controla |
|---|---|---|
| `LLM_PROVEEDORES` | `groq,gemini` | Orden de intento de los proveedores de LLM. Ver "Fallback entre proveedores de LLM" abajo. |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Modelo de generación de Gemini. |
| `GROQ_MODEL` | `openai/gpt-oss-20b` | Modelo de generación de Groq. |
| `RAG_RUTA_CORPUS` | `src/rag/corpus` | Carpeta con los `.md` del corpus normativo. |
| `RAG_RUTA_INDICE` | `rag_index/` en la raíz | Carpeta donde persiste el índice Chroma. |
| `RAG_MODELO_EMBEDDINGS` | `paraphrase-multilingual-MiniLM-L12-v2` | Modelo HuggingFace de embeddings. |
| `RAG_K_RESULTADOS` | `5` | Cuántos chunks recuperar antes de filtrar por umbral. |
| `RAG_UMBRAL_SIMILITUD` | `0.45` | Umbral mínimo de similitud. Si la primera búsqueda no supera el umbral, se reintenta una vez con la pregunta reformulada por un LLM (fallback de retrieval); si tampoco, el servicio se abstiene sin generar una respuesta. |
| `RAG_UMBRAL_FUENTES` | `0.50` | Umbral mínimo, más estricto que `RAG_UMBRAL_SIMILITUD`, para que un chunk se liste en `fuentes`. No afecta qué contexto recibe el LLM para generar la respuesta, solo qué se muestra como fuente — evita listar chunks temáticamente cercanos pero no la razón real de la respuesta. |

### SDK de Gemini

Usa **`google-genai`**, no `google-generativeai`: Google deprecó ese segundo
paquete —el que usa el notebook de prototipo, `RAG_Gemini_ANH.ipynb`— sin más
actualizaciones ni corrección de bugs. No migrar el servicio de vuelta a
`google-generativeai`, aunque el notebook siga siendo la referencia del
pipeline (chunking → embeddings → Chroma → retrieval → generación).

### Fallback entre proveedores de LLM

Gemini falla de forma intermitente por saturación (`503 UNAVAILABLE`). Para
no depender de un solo proveedor durante la demo, `rag_core.py` intenta los
proveedores listados en `LLM_PROVEEDORES` en orden: cada uno agota 3
reintentos con backoff exponencial (1s, 2s, 4s) ante errores transitorios
(saturación, límite de tasa, timeout, conexión) antes de pasar al siguiente.
Errores no transitorios (API key inválida, request mal formado) no se
reintentan: pasan directo al siguiente proveedor. Si todos fallan, el
servicio responde `500` con el mismo mensaje de siempre
("El servicio de generación no respondió correctamente."); esto es distinto
de la abstención del contrato (`encontrado: false`), que ocurre solo cuando
el *retrieval* no encuentra chunks relevantes, no cuando falla la generación.

`LLM_PROVEEDORES` permite cambiar el orden o sacar un proveedor entero
editando el `.env` y reiniciando el contenedor, sin tocar código — pensado
como mitigación rápida si un proveedor tiene una intermitencia larga durante
la demo grabada (por ejemplo, `LLM_PROVEEDORES=gemini` para operar solo con
Gemini si Groq no responde). El selector de proveedor es enteramente interno
al servicio RAG: no hay ningún control de esto en la interfaz de chat.

---

## Servicio de validación de imágenes

`src/validacion_imagenes`, puerto 8004. Verifica que la foto que el
ciudadano sube en el Paso 3 del chat muestre, con claridad y sin
sobreposiciones, un rostro humano y una cédula de identidad sostenida por
esa persona. Como el RAG, es un componente real: no simula un sistema
externo, resuelve una parte genuina del trámite.

**Es un pre-filtro automático, no reemplaza al evaluador humano.** Solo
verifica presencia y oclusión (¿hay un rostro?, ¿hay una cédula?, ¿algo los
tapa?). No evalúa legibilidad fina del documento, vigencia, ni que el rostro
corresponda a la persona registrada en Ciudadanía Digital — el criterio
final sobre la foto sigue siendo del evaluador, igual que antes de que
existiera este servicio.

**Bloquea el envío.** Se llama desde la interfaz de chat al hacer clic en
"Continuar" en el Paso 3, antes de armar y enviar la solicitud a Backend
ANH. Si el veredicto es `INVALIDA`, o si el servicio no responde, el chat no
avanza al paso siguiente: le pide al ciudadano otra foto. La solicitud nunca
llega a Backend ANH con una foto que no pasó esta validación.

### Levantar el servicio

**Local:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-validacion-imagenes.txt

cd src
uvicorn validacion_imagenes.main:app --reload --port 8004
```

**Docker:**

```bash
docker compose up validacion-imagenes
```

### Variables de entorno

Reusa `GOOGLE_API_KEY` (misma cuenta de Gemini que el servicio RAG). Falla
al arrancar con un mensaje explícito si falta.

Opcionales, con default razonable:

| Variable | Default | Qué controla |
|---|---|---|
| `VALIDACION_IMAGENES_MODELO_GEMINI` | `gemini-3.1-flash-lite` | Modelo de visión de Gemini. Mismo modelo que usa RAG por defecto, pero en una variable propia (no `GEMINI_MODEL`): ambos servicios reciben el mismo `.env` vía `docker-compose.yml`, y cada uno puede necesitar cambiar de modelo sin afectar al otro. Modelos más nuevos (ej. `gemini-3.8-flash`) tienen cuotas gratuitas mucho más bajas (20 solicitudes/día) y devolvieron JSON estructurado mal formado en las pruebas; `gemini-3.1-flash-lite` funcionó de forma confiable. |
| `VALIDACION_IMAGENES_PROVEEDORES` | `gemini` | Proveedores de visión a intentar, en orden. Hoy solo Gemini tiene un modelo de visión confirmado; Groq (`openai/gpt-oss-20b`, el default del RAG) es un modelo de texto, sin visión. El mecanismo queda extensible por si en el futuro se confirma un modelo de Groq con visión estable. |
| `VALIDACION_IMAGENES_MAX_BYTES` | `8388608` (8 MB) | Tamaño máximo aceptado de la imagen decodificada. |

---

## Interfaz de chat

`src/chat_web`, puerto 8080. HTML/CSS/JS **vanilla**: sin build step, sin
npm, sin framework — archivos que el navegador sirve tal cual. Consume los
cuatro servicios (`backend_anh`, `ciudadania_digital`, `rag`,
`validacion_imagenes`) directo desde el navegador vía `fetch`, replicando la
misma lógica de armado de solicitudes, manejo de errores e idempotencia que
tendría cualquier cliente del contrato estándar.

Reemplaza un prototipo anterior hecho en Streamlit: se migró porque ajustar
el diseño visual al mockup aprobado exigía pelear contra el DOM interno de
Streamlit (`data-testid`s que cambian según qué widget está presente, gaps
de layout no documentados), lo que hacía cada iteración visual más costosa
de lo que valía. Con HTML/CSS propio el control del DOM es directo.

### Levantar la interfaz

Los cuatro servicios backend tienen que estar corriendo primero (`docker
compose up`, o cada uno localmente). Después:

```bash
cd src
uvicorn chat_web.server:app --port 8080 --reload
```

Sirve en `http://localhost:8080`. `server.py` monta `catalogos/` y
`recursos/` directo desde la raíz del repo (mismos archivos que usan los
otros servicios, sin duplicarlos) además de los archivos propios de
`src/chat_web/static/`.

### Por qué CORS

`fetch` desde el navegador está sujeto a CORS; las llamadas Python
servidor-a-servidor no lo estaban. Por eso los cuatro servicios backend tienen
`CORSMiddleware` con `allow_origins=["*"]` (ver "Decisiones cerradas" abajo).

---

## Por qué importa el video

El entregable final de la maestría es un **video donde cada integrante muestra el
prototipo**, grabado en su propia máquina. De ahí varias decisiones: nada de
hosting remoto, arranque rápido, datos de semilla compartidos para que las tres
demostraciones sean coherentes, y endpoint de reinicio.

Probar el arranque completo del entorno antes del día de grabar, no ese mismo día.

---

## Stack y convenciones

- **Python + FastAPI**, un archivo o módulo por servicio backend.
- **Docker Compose** para levantar los cuatro contenedores backend.
- `/docs` de FastAPI queda disponible en cada servicio (Swagger UI automático).
- La **interfaz de chat es HTML/CSS/JS vanilla**: sin build step, sin npm,
  sin framework. No agregar uno para esto sin una razón concreta que lo
  justifique — es la decisión que motivó dejar Streamlit.

**Convenciones:**

- **Todo en español**: nombres de campos, mensajes, comentarios, documentación.
- Los códigos de error (`codigo`) son identificadores estables en mayúsculas con
  guión bajo, para la lógica del cliente. El `mensaje` es texto legible, apto
  para mostrar al ciudadano.
- El código de trámite tiene formato `ANH-AAAA-XXXXXX` (año + 6 caracteres
  alfanuméricos en mayúsculas, tomados de un UUID), deliberadamente corto para
  que una persona pueda dictarlo por teléfono. Al generarlo se verifica que no
  exista ya en la base y se regenera si choca. Las solicitudes de las semillas
  llevan códigos fijos, iguales en cada corrida, para grabar el video siempre
  con los mismos ejemplos.
- El `motivo_rechazo` se redacta para que el solicitante entienda qué corregir,
  no como código interno.

**Nota sobre direcciones:** `localhost:8001` funciona desde el navegador, pero no
entre contenedores. Si otro contenedor consume estos servicios, la dirección es
el nombre del servicio en Docker Compose (`http://backend-anh:8001`). Eso va en
la configuración del consumidor, no en la spec.

---

## Fuera de alcance

- Integración con sistemas reales de la ANH o de AGETIC
- Autenticación y autorización de producción
- Notificación de eventos hacia el asistente
- PostgreSQL u otro motor con servidor propio
- Despliegue remoto (Render, Fly.io y similares)
- Verificación biométrica de que el rostro corresponde a la persona registrada en Ciudadanía Digital
- Validación de autenticidad del documento de identidad (hologramas, MRZ, etc.)
