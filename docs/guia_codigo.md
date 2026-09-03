# Guia de lectura del codigo

Este documento resume como esta organizado el MVP del asistente RAG ANH y que
papel cumple cada archivo. Sirve como apoyo para el equipo durante la defensa o
para que otro integrante pueda continuar el desarrollo.

## Flujo general

1. El usuario abre `http://127.0.0.1:8000`.
2. `src/app.py` muestra una interfaz web con chat guiado, seguimiento y panel
   evaluador.
3. Cuando el usuario envia un mensaje, `src/app.py` lo entrega a
   `ConversationSession` en `src/conversation.py`.
4. Si el mensaje es una consulta normativa, `ConversationSession` llama a
   `LexicalRAG` en `src/rag_engine.py`.
5. `LexicalRAG` busca fragmentos en `data/corpus_normativo.json`, calcula un
   puntaje de relevancia y devuelve respuesta con fuentes.
6. Si el usuario inicia registro, `ConversationSession` avanza por una maquina
   de estados: CI, actividad, zona, combustible, volumen, destino, foto y
   confirmacion.
7. Al confirmar, el backend simulado verifica el CI, valida el volumen declarado
   y guarda la solicitud en `data/solicitudes_demo.json`.
8. El usuario puede consultar el estado con el codigo generado.
9. El panel evaluador permite cambiar el estado a `pendiente`, `aprobada` o
   `rechazada`.

## Archivos principales

### `src/rag_engine.py`

Contiene el motor de recuperacion del MVP. Actualmente no usa embeddings ni una
base vectorial real; usa una estrategia lexica tipo TF-IDF simplificada para
mantener la demo reproducible sin API externa.

Elementos importantes:

- `TOKEN_RE`: expresion regular para separar texto en palabras.
- `SYNONYMS`: sinonimos minimos para mejorar consultas del dominio.
- `Chunk`: representa un fragmento del corpus con fuente y seccion.
- `RetrievalResult`: une un fragmento con su puntaje de relevancia.
- `LexicalRAG.retrieve()`: recupera los fragmentos mas relevantes.
- `LexicalRAG.answer()`: genera una respuesta orientativa con fuentes.

Esta clase se puede reemplazar posteriormente por ChromaDB o FAISS si se
conservan los metodos `retrieve()` y `answer()`.

### `src/backend_simulado.py`

Simula los sistemas institucionales que no estan disponibles para el prototipo.

Elementos importantes:

- `CIUDADANIA_DIGITAL`: base simulada de personas registradas.
- `verificar_ciudadania_digital()`: confirma si un CI existe en la base simulada.
- `validar_volumen()`: aplica limites de volumen por zona.
- `crear_solicitud()`: genera codigo de tramite y guarda la solicitud.
- `consultar_solicitud()`: permite seguimiento por codigo y CI.
- `actualizar_estado()`: permite aprobar o rechazar desde el panel simulado.

### `src/conversation.py`

Contiene la maquina de estados del registro conversacional.

Estados principales:

- `idle`: espera una consulta normativa o la orden de iniciar registro.
- `ask_ci`: solicita y valida el Carnet de Identidad simulado.
- `ask_activity`: captura la actividad del interesado.
- `ask_zone`: valida si la zona es nacional o fronteriza.
- `ask_fuel`: valida gasolina o diesel.
- `ask_volume`: valida el volumen contra la regla de negocio.
- `ask_destino`: captura el destino de uso.
- `ask_photo`: simula la carga de fotografia.
- `confirm`: muestra resumen y registra la solicitud si el usuario confirma.

### `src/app.py`

Implementa la interfaz web local usando librerias estandar de Python.

Rutas principales:

- `GET /`: muestra la pagina principal.
- `POST /chat`: procesa mensajes del asistente conversacional.
- `POST /reset`: reinicia el historial y los datos capturados.
- `POST /status`: consulta el estado de una solicitud.
- `POST /update`: actualiza el estado desde el panel evaluador.

La variable `Handler.state` mantiene los valores visibles en pantalla durante la
demo. No es una sesion multiusuario; es suficiente para el escenario academico.

### `eval/evaluate_rag.py`

Ejecuta una prueba top-3 del recuperador. La evaluacion verifica si la fuente
esperada aparece entre los tres primeros fragmentos recuperados para cada
consulta de `eval/test_queries.json`.

Comando:

```bash
python eval/evaluate_rag.py
```

El umbral minimo configurado es 80 %. Si la precision queda por debajo de ese
valor, el script termina con error.

## Datos de prueba

Carnets de Identidad simulados:

- `1234567`: Ana Choque Mamani.
- `7654321`: Victor Hugo Flores.
- `4567890`: Rafael Quispe Condori.

Estados de solicitud:

- `pendiente`
- `aprobada`
- `rechazada`

## Siguiente mejora tecnica

El siguiente paso recomendado es implementar una segunda version del recuperador
con embeddings y una base vectorial. Para hacerlo sin romper la app actual:

1. Crear `src/vector_rag_engine.py`.
2. Mantener los metodos `retrieve(query, top_k=3)` y `answer(query)`.
3. Cambiar en `src/app.py` la instancia `LexicalRAG` por el nuevo motor.
4. Ejecutar `python eval/evaluate_rag.py` o adaptar el evaluador al nuevo motor.
