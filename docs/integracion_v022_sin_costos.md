# Integracion v0.2.2 sin consumo externo

Fecha: 2026-09-27

## Incorporado al piloto

- Validacion local del limite de volumen usando `catalogos/ubicaciones.json`.
- Limite de 50 litros para municipios fronterizos.
- Limite de 120 litros para municipios no fronterizos.
- Mensaje visible del limite aplicable antes de continuar el registro.
- Preguntas manuales para evaluar el RAG en `asistente-anh/src/rag/evaluacion/preguntas-rag.md`.

Estas validaciones se ejecutan en el navegador y no llaman a Gemini ni a otro proveedor externo.

El proveedor predeterminado del RAG queda fijado en `groq`; Gemini solo se activa si se configura de forma explícita mediante `LLM_PROVEEDORES` y `GOOGLE_API_KEY`.

## Reservado para una fase posterior

- Servicio de validacion de imagenes con Gemini.
- Activacion de `GOOGLE_API_KEY` para validar fotografias.
- Cambios experimentales del runtime del RAG y del corpus ampliado, hasta completar la evaluacion local.

El piloto conserva el flujo de fotografias existente sin validacion automatica externa. Para mantener el costo controlado, cualquier prueba de vision debe ejecutarse en una ventana acotada, con una clave separada y limites de cuota revisados.

La prueba experimental de Gemini y sus resultados estan documentados en `docs/evidencias/prueba_gemini_free_tier_20260927.md`.
