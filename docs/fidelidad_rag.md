# Fidelidad del RAG: selección de evidencia y abstención

## Problema reproducido

La evaluación de la imagen CPU mostró que una pregunta con historial podía
producir ejemplos de fotos del recipiente o lugar de uso no enumerados en el
corpus. El refuerzo del prompt de redacción no eliminó ese comportamiento.

## Cambio de comportamiento

La ruta `/v1/consultas-rag` ahora usa el LLM para seleccionar los identificadores
de los fragmentos que responden la pregunta. El servidor valida el JSON y
publica el texto literal de esos fragmentos, con una introducción y advertencia
fijas. No publica prosa libre generada por el modelo en esta ruta.

- Selección vacía, formato inválido, claves extra, IDs fuera de rango o
  duplicados: abstención sin fuentes.
- Las fuentes corresponden exactamente a los fragmentos publicados.
- El historial solo ayuda a interpretar la pregunta; no se usa como evidencia.
- Si se reformula una consulta para recuperar documentos, la selección final
  sigue evaluándose contra la pregunta original.
- Groq y Gemini reciben una solicitud de JSON para esta selección, con un
  límite de salida mayor. La generación del texto de seguimiento no cambia.

Las respuestas normativas pueden ser más largas y menos conversacionales.
Se conservan fragmentos completos para no eliminar negaciones o condiciones
mediante recortes automáticos. No cambian las rutas ni los campos de respuesta.

## Recuperación

Se observó un falso negativo reproducible: la pregunta sobre fotografías y
datos personales recupera el artículo 4 con similitud **0,4267**. El umbral
anterior de 0,45 lo excluía y hacía depender la respuesta de una reformulación
variable. El valor predeterminado se ajustó a **0,40**, configurable mediante
`RAG_UMBRAL_SIMILITUD`. En los casos de diagnóstico, la consulta de receta dio
0,0296 como máximo y la pregunta ambigua sin contexto, 0,1455.

Es una calibración sobre este corpus pequeño, no un umbral universal. La
selección del modelo sigue comprobando si los fragmentos contienen el dato
solicitado; la similitud por sí sola no decide la respuesta.

## Pruebas reproducibles

Desde `asistente-anh/`:

```bash
python -m pytest -q
# Con dependencias RAG instaladas:
PYTHONPATH=src python eval/test_motor_evidencia.py
# Contra un servicio con este cambio; consume cuota de Groq:
python eval/validar_rag.py --url http://localhost:18003 --repeticiones 3 \
  --report ../docs/evidencias/fidelidad_rag_v2.json
```

La suite HTTP tiene 12 casos: requisitos, fotografías, pregunta con contexto,
tema ajeno, dato personal ausente, volumen no documentado, foto del recipiente,
plazo ausente, ambigüedad, historial que afirma un requisito falso, petición de
ejemplos no documentados e instrucciones adversas.

Además de fuentes y abstención, comprueba que la respuesta sea exactamente la
composición de los fragmentos publicados y los mensajes fijos. Esto detecta
prosa añadida por el modelo; no demuestra pertinencia semántica para cualquier
pregunta. Las respuestas siguen requiriendo revisión humana.

La evaluación inicial de selección de evidencia obtuvo **35/36**: falló por
una abstención en fotografías, sin publicar texto inventado. Se conserva en
[evidencia inicial](evidencias/fidelidad_rag_v2_inicial.json).

## Resultado final

- **50 pruebas locales aprobadas**, incluidas 13 de validación de selección.
- **5 pruebas del orquestador aprobadas** dentro de la imagen RAG.
- **36/36 consultas HTTP aprobadas**: 12 casos repetidos tres veces con Groq.
  Las nueve respuestas con evidencia reprodujeron los fragmentos seleccionados;
  las 27 consultas sin respaldo suficiente se abstuvieron.
- Se revisaron las respuestas positivas contra sus fragmentos: no se añadieron
  ejemplos de fotos del recipiente ni del lugar de uso.

[Evidencia final](evidencias/fidelidad_rag_v2.json). El caso de fotografías pasó
las tres veces con el umbral 0,40, sin depender de reformular esa pregunta.
Los resultados describen este conjunto controlado; no equivalen a precisión
universal del sistema.

## Ejecución local

La imagen validada se activó en el servicio RAG local (puerto 8003) para que la
interfaz habitual en http://localhost:8081 use la nueva respuesta extractiva.
Se retiró el contenedor temporal de pruebas. No se modificaron las bases de
datos de solicitudes. Los cambios se entregan como `v0.2.1` en `main`;
la etiqueta `v0.2.0` conserva la entrega anterior.

## Aceptación de la interfaz y cierre

El usuario comunicó que las pruebas de la nueva respuesta extractiva resultaron
positivas. Esta aceptación se registra como validación manual declarada, sin
atribuirle capturas o pruebas automatizadas adicionales. La entrega `v0.2.1`
incluye esta mejora y la optimización CPU; conserva las limitaciones siguientes.

## Límites

- El modelo todavía puede seleccionar evidencia poco pertinente o abstenerse
  cuando existe una respuesta. Los extractos literales no garantizan relevancia.
- La calidad y vigencia del corpus no se verifican con estas pruebas.
- No se infiere que un requisito no exista solo porque no figure en el corpus.
- El texto de seguimiento conserva generación libre; este cambio se limita a
  consultas normativas.
- Se verificó Groq; el modo JSON de Gemini requiere validación con credenciales
  de ese proveedor antes de considerarlo probado.
- Esta rama incluye la optimización CPU anterior; no modifica la etiqueta v0.2.0.
