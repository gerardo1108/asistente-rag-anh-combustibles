# Evidencia de prueba Gemini en nivel gratuito

Fecha: 2026-09-27
Rama: `experimento/gemini-free-tier`

## Configuracion

- Proyecto AI Studio: `asistente`.
- Estado observado: `Nivel gratuito`.
- Facturacion: no configurada.
- Modelo: `gemini-3.1-flash-lite`.
- La API key se mantuvo solo en `.env`, excluida por `.gitignore`.
- No se incorporaron claves ni secretos al repositorio.

## Pruebas realizadas

1. Consulta minima de texto a Gemini: respuesta `PRUEBA_GEMINI_OK`.
2. Validacion del logotipo ANH: resultado `INVALIDA`, codigo `ROSTRO_NO_VISIBLE`.
3. Validacion de imagen sintetica con rostro y documento simulado: resultado `VALIDA`.
4. Verificacion con el servicio desactivado: respuesta `503 VALIDACION_IMAGENES_DESACTIVADA`, sin llamada al proveedor.
5. Pruebas locales con proveedor simulado: imagen valida, base64 invalido y MIME no soportado.

## Control de consumo

- Las llamadas reales a Gemini fueron puntuales y manuales.
- La validacion real se ejecuto con un solo intento y sin reintentos.
- La bandera permanente `VALIDACION_IMAGENES_ACTIVA` permanece desactivada por defecto.
- No se utilizaron fotografias de personas reales ni documentos reales.

## Resultados automatizados

La suite completa termino con **74 pruebas exitosas** y **2 subpruebas exitosas**. Quedaron dos advertencias informativas de dependencias, sin fallos funcionales.

## Estado

La integracion experimental funciona, pero no se incorpora al piloto estable hasta definir limites de uso, privacidad, monitoreo de cuota y una decision explicita sobre activar Gemini en el flujo ciudadano.
