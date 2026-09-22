# Estado de validación de la V2

Fecha: 22 de septiembre de 2026.

## Versiones

- V1: etiqueta local `v0.1.0`, commit `3553700`.
- Base V2: aporte de Helmuth, commit `9ab208c`.
- Preparación: rama `integracion/v2-interfaz-helmuth`.
- `main` permanece en la V1. No se ha creado `v0.2.0`.

La interfaz y el flujo de `asistente-anh/` son la base acordada. La V1 se
conserva como referencia histórica durante la transición.

## Cambios de preparación

- Interfaz y supervisor incluidos en Docker Compose, puerto 8081 por defecto.
- Volúmenes persistentes separados para ambas bases SQLite.
- Puertos públicos configurables y compartidos por chat y supervisor.
- README principal orientado a V2; instrucciones V1 identificadas como históricas.
- `.env` local con Groq configurado; backend en 18001 porque una instancia anterior ocupa 8001.
  Las claves están excluidas de Git y no se incluyen en esta documentación.

## Evidencia

Desde `asistente-anh/`, con `requirements-dev.txt` instalado:

```bash
python -m pytest -q
```

Resultado: **37 pruebas aprobadas**, con dos avisos de deprecación de las
bibliotecas de pruebas. Incluye las 33 pruebas existentes y cuatro casos
adicionales: identidad → registro con adjunto sintético → aprobación/rechazo
→ seguimiento → reapertura de SQLite; entrega HTTP de páginas y recursos;
y configuración de puertos sin exponer secretos.

Los casos de flujo usan TestClient y bases temporales. No equivalen a una
prueba visual del navegador ni validan el contenido fotográfico.

Docker Compose: configuración validada; imágenes de backend, ciudadanía y
chat construidas y contenedores iniciados. Chat, supervisor, configuración
JavaScript y endpoints de salud comprobados por HTTP.

## Acceso local

- Chat: http://localhost:8081
- Supervisor: http://localhost:8081/supervisor
- Backend: http://localhost:18001
- Ciudadanía Digital: http://localhost:8002
- Identidades habilitadas de prueba: `6789012` y `4521987`.

Para detener estos servicios sin eliminar las bases:

```bash
cd asistente-anh
docker compose stop backend-anh ciudadania-digital chat
```

En este Mac el CLI de Homebrew no detecta el complemento Compose. Se utilizó
`/Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose`
como sustituto de `docker compose`.

## Pendientes antes de v0.2.0

1. Ampliar la evaluación del RAG más allá de las tres comprobaciones iniciales.
2. Completar la prueba visual de registro con foto, revisión y seguimiento.
   No hay un navegador conectado a la herramienta de verificación de esta sesión.
3. Acordar las validaciones del flujo V2. Los límites simulados de V1 no se
   trasladaron automáticamente a la propuesta de Helmuth.
4. Verificar conservación de solicitudes al recrear contenedores, además de
   la reapertura de SQLite ya cubierta por pruebas.
5. Revisar los resultados antes de incorporar la rama a main y etiquetar v0.2.0.

## Activación y comprobación inicial del RAG

Groq configurado con `LLM_PROVEEDORES=groq` y modelo `openai/gpt-oss-20b`.
Autenticación y disponibilidad del modelo verificadas. Imagen Docker
construida, índice Chroma generado con 8 fragmentos y servicio iniciado en
http://localhost:8003. No se necesita clave de Gemini en este modo.

Pruebas HTTP realizadas el 22 de septiembre de 2026:

| Caso | Resultado | Tiempo observado |
|---|---|---|
| Información mínima del formulario | Respuesta de Groq, `encontrado=true`, 3 fuentes; el artículo 4 aparece primero | 0,71 s |
| Receta de tarta de chocolate | Abstención, `encontrado=false`, sin fuentes | 0,71 s |
| Estado de trámite sintético | Texto con código y estado REGISTRADO | 0,44 s |

Evidencia completa: [validacion_rag_groq.json](evidencias/validacion_rag_groq.json).
Son comprobaciones de funcionamiento sobre el corpus incluido, no una
medición representativa de precisión ni una verificación jurídica del corpus.
El texto de estado menciona una notificación futura aunque el prototipo solo
ofrece consulta activa; revisar esa instrucción antes de la demostración final.
La validación visual integral y la biometría no están verificadas.

La primera construcción descargó dependencias grandes de PyTorch/CUDA aunque
los embeddings se ejecutan en CPU. Queda como mejora reducir la imagen mediante
una instalación de PyTorch para CPU; no impidió el arranque ni estas pruebas.
