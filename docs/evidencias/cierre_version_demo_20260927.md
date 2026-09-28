# Cierre de versión candidata para demo

Fecha de cierre: 2026-09-27  
Rama: `plan/persistencia-demo`  
Commit de referencia: `336e3c9`

## Estado

Esta versión queda fijada como **versión candidata final para el demo**. No se
realizarán cambios funcionales adicionales antes de la implementación de la
ventana de pruebas del día siguiente, salvo correcciones críticas de arranque
o disponibilidad.

## Funcionalidades incluidas

- Consulta normativa RAG con respuestas breves y fuentes verificables.
- Saludo inicial sin enviar consultas innecesarias al RAG.
- Contexto de la pregunta anterior para seguimientos conversacionales.
- Corpus ampliado con normativa ANH, Ciudadanía Digital, límites y glosario.
- Registro completo del formulario con datos sintéticos.
- Navegación hacia pasos anteriores conservando los datos capturados.
- Validación de imagen con Gemini para rostro y documento visibles.
- Persistencia local de trámites mediante volúmenes Docker.
- Panel de supervisor para aprobar, rechazar y reabrir trámites.
- Reapertura controlada: un trámite resuelto vuelve a `REGISTRADO` antes de
  admitir una nueva decisión.

## Validación realizada

- Suite automatizada: **55 pruebas exitosas** y una advertencia informativa.
- Flujo manual completo: registro, imagen, generación de código, aprobación y
  consulta posterior del estado.
- Batería manual de Helmut: **20 preguntas ejecutadas** con pausas para
  respetar la cuota gratuita de Gemini.
- Solicitudes RAG observadas en logs durante la batería: 21, incluyendo una
  consulta adicional de verificación.
- No se observaron errores `429` ni `500` durante la batería pausada.
- Se verificaron respuestas correctas para límites nacionales, zonas
  fronterizas, fotografías, registro desde celular y Ciudadanía Digital.
- Las preguntas sin respaldo explícito produjeron abstención en lugar de
  inventar información.

## Alcance de la demo

- Usar exclusivamente datos, identidades e imágenes sintéticas.
- La validación Gemini consume cuota del nivel gratuito de AI Studio; las
  pruebas deben ejecutarse de forma pausada y evitando consultas repetidas.
- La respuesta sobre maquinaria agrícola es descriptiva y no confirma una
  excepción normativa especial.
- El enlace HTTPS temporal depende de que esta computadora, Docker y
  `cloudflared` permanezcan activos.

## Implementación prevista para mañana

1. Levantar los contenedores desde esta rama y commit de referencia.
2. Regenerar el índice RAG si la implementación cambia de máquina.
3. Comprobar chat, RAG, backend, Ciudadanía Digital y validación de imágenes.
4. Confirmar el enlace HTTPS temporal.
5. Ejecutar una prueba corta de saludo, consulta RAG, registro y supervisor.
6. Compartir el enlace con el equipo para la confirmación final de la versión
   que se utilizará en el demo.

## Referencias

- `docs/evidencias/prueba_piloto_manual_20260927.md`
- `docs/evidencias/prueba_gemini_free_tier_20260927.md`
- `asistente-anh/src/rag/evaluacion/preguntas-rag.md`

