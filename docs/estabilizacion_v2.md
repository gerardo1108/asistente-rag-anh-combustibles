# Estabilización de la V2 — 22 de septiembre de 2026

## Alcance

Versión `v0.2.0` para demostración académica con la interfaz y el flujo de
Helmuth. Conserva servicios ANH y Ciudadanía Digital simulados y generación
RAG real mediante Groq. La V1 se conserva en la etiqueta `v0.1.0`.

## Prueba de interfaz comunicada por el usuario

El usuario realizó el recorrido propuesto y comunicó que el resultado fue
positivo: consulta normativa, pregunta fuera de alcance, registro con imagen
de prueba, seguimiento, aprobación en el supervisor y nueva consulta del
estado. Es evidencia declarada por el usuario; no hay grabación ni captura
adjunta de esa ejecución. No se atribuye a una prueba automatizada.

## Correcciones

- El estado REGISTRADO invita a consultar nuevamente con el código del trámite.
  Se eliminó la promesa de notificación del prompt y del ejemplo OpenAPI y
  se alinearon los mensajes de respaldo del servidor y del navegador.
- El prompt normativo pide no añadir ejemplos de fotografías, documentos o
  destinos que no estén enumerados en el corpus. En la evaluación inicial,
  una pregunta con contexto provocó ejemplos de fotos no sustentados; la
  evidencia inicial se conserva para distinguir el problema de la corrección.

## Resultados finales

- Suite funcional: **37 pruebas aprobadas** (dos avisos de deprecación).
- Persistencia: **5 de 5 solicitudes conservadas íntegramente** después de
  recrear los contenedores; una es la solicitud sintética de esta comprobación.
- RAG: cinco comprobaciones automáticas aprobadas y un caso de volumen revisado
  manualmente, con abstención. También se revisó el contenido de las seis
  respuestas finales; no se repitieron los ejemplos de fotos ajenos al corpus.
- Seguimiento: tres respuestas REGISTRADO invitan a consultar nuevamente y no
  prometen notificaciones.

Evidencias:

- [Persistencia Docker](evidencias/persistencia_docker_v2.json).
- [Evaluación RAG inicial](evidencias/evaluacion_rag_v2_inicial.json).
- [Evaluación RAG corregida](evidencias/evaluacion_rag_v2.json).
- [Seguimiento corregido](evidencias/seguimiento_v2.json).

## Reproducir las comprobaciones

Desde `asistente-anh/`, para las pruebas sin proveedores externos:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Con el RAG activo y claves configuradas, las siguientes consultas consumen
cuota del proveedor y guardan respuestas para revisión humana:

```bash
python eval/validar_rag.py --report ../docs/evidencias/evaluacion_rag_v2.json
```

El programa comprueba fuentes y abstención en un conjunto pequeño. Las
respuestas deben revisarse además para detectar detalles no sustentados.
No representa una medición general de precisión ni garantiza ausencia de
alucinaciones. No verifica la vigencia jurídica de los documentos.

Para reconstruir los componentes modificados conservando datos:

```bash
docker compose up -d --build rag chat
```

En este Mac se usa el ejecutable
`/Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose`
en lugar de `docker compose`.

## Límites de esta entrega

- El registro y la identidad son simulados; no hay conexión con entidades reales.
- Las fotografías se almacenan, pero no se verifica identidad ni biometría.
- El seguimiento es por consulta activa; no se envían notificaciones.
- Los límites de volumen simulados de V1 no se trasladaron al flujo V2.
- Las fuentes mostradas son los fragmentos recuperados, no una garantía de que
  cada uno haya sido utilizado en la respuesta generada.
- Los proveedores pueden imponer cuotas y las respuestas pueden variar.
- La autenticación de los mocks no constituye control de acceso para producción.
- Reducir el tamaño de la imagen Docker queda como mejora posterior.

## Cierre de versión

Esta estabilización se entrega como `v0.2.0` en `main`, conservando la V1 en
`v0.1.0`. El cierre incluye las correcciones y evidencias descritas arriba;
las limitaciones documentadas permanecen vigentes.
