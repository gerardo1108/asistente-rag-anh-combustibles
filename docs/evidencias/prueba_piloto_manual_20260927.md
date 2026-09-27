# Cierre de prueba manual del piloto

Fecha: 2026-09-27  
Rama: `plan/persistencia-demo`  
Commit: `5e5d4d1`

## Entorno

- Acceso local: `http://127.0.0.1:18080/`.
- Servicios ejecutados con Docker Compose.
- Backend: puerto local `18001`.
- Ciudadanía Digital: puerto local `18002`.
- RAG: puerto local `18003`.
- Supervisor: `http://127.0.0.1:18080/supervisor`.
- Índice RAG reconstruido con 10 fragmentos.
- Validación de imágenes Gemini desactivada para el piloto estable.
- Gemini utilizado únicamente para las consultas de texto del RAG, con el
  proyecto de AI Studio en nivel gratuito y sin facturación configurada.

## Flujo ejecutado por agente humano

1. Consulta de información normativa dentro del ámbito del asistente.
2. Registro de un trámite con datos sintéticos.
3. Carga de la imagen sintética
   `asistente-anh/recursos/pruebas/documento-simulado-sin-identidad.png`.
4. Aceptación de la declaración jurada y envío del formulario.
5. Obtención y conservación del código de trámite.
6. Localización del trámite en el panel de supervisor.
7. Aprobación del trámite.
8. Consulta posterior del estado mediante el código generado.

Resultado: **flujo completo aprobado manualmente**.

## Consultas RAG verificadas

- Límite mensual en territorio nacional: respuesta con referencia al límite
  de 120 litros.
- Límite mensual en zonas fronterizas: respuesta con referencia al límite de
  50 litros.
- Destino para maquinaria agrícola: el asistente indicó correctamente que
  el corpus no contiene una instrucción agrícola específica. Se validó como
  descripción de prueba `Combustible para maquinaria agrícola`, sin afirmar
  una excepción normativa.
- Implicaciones legales del formulario: respuesta con advertencia sobre la
  calidad de declaración jurada y referencia normativa.

## Incidente corregido durante la preparación

La primera reconstrucción del contenedor RAG seleccionó `groq` sin disponer de
`GROQ_API_KEY`, lo que provocaba un error HTTP 500 al consultar. Se volvió a
seleccionar `gemini`, proveedor ya configurado para este entorno, y se recreó
únicamente el servicio RAG. La consulta de límites respondió correctamente
después del ajuste.

## Alcance y pendientes

- La validación es manual y utiliza datos e imagen sintéticos.
- No se validan identidades ni documentos reales.
- La validación fotográfica con Gemini permanece fuera del piloto estable.
- La respuesta sobre maquinaria agrícola no constituye interpretación oficial
  ni confirma un límite especial no incluido en el corpus.
- El acceso usado en esta evidencia es local; no es todavía una URL pública.

