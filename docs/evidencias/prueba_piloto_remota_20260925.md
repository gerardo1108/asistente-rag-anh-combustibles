# Evidencia de prueba remota del piloto

## Identificación

- Versión funcional: `v0.2.1`
- Commit probado: `02f47b1`
- Modalidad: Docker local con Quick Tunnel temporal
- Datos: exclusivamente sintéticos
- Fecha de la prueba: 2026-09-25

## Configuración

El piloto se levantó con cuatro servicios: chat, Backend ANH, Ciudadanía Digital y RAG. El chat actuó como proxy de las APIs internas, por lo que los usuarios remotos utilizaron una sola URL HTTPS y no necesitaron acceder a puertos adicionales.

La URL temporal utilizada fue:

`https://jun-figured-boss-pontiac.trycloudflare.com`

Esta URL fue válida únicamente durante la sesión y no debe reutilizarse en la prueba siguiente.

## Comprobaciones realizadas

- La interfaz web cargó desde HTTPS.
- El registro ciudadano funcionó con la tarjeta sintética de Juan Carlos Mamani Quispe.
- Se generó un código de trámite.
- La consulta normativa respondió con fuentes del corpus.
- La solicitud apareció en el panel supervisor.
- El supervisor pudo aprobar la solicitud.
- La consulta de estado devolvió el estado aprobado.
- El acceso funcionó desde una URL pública temporal.

## Incidencia observada

En la primera consulta de estado se ingresó `NH-2026-959692`, omitiendo la primera letra del prefijo. El código correcto era `ANH-2026-959692`. Al repetir la consulta con el código completo, el sistema devolvió `APROBADO`.

La incidencia correspondió a un error de digitación y no a una falla del sistema.

## Resultado

La prueba remota de extremo a extremo fue satisfactoria. El piloto está preparado para repetir el despliegue durante una ventana controlada, generando una nueva URL temporal y cerrando el túnel al finalizar.

## Repetición mañana

1. Iniciar Docker Desktop.
2. Levantar el Compose con puertos aislados.
3. Ejecutar el smoke test.
4. Iniciar un Quick Tunnel sobre el puerto `18080`.
5. Compartir la nueva URL HTTPS con el equipo.
6. Ejecutar las pruebas del paquete con datos sintéticos.
7. Cerrar el túnel y detener los contenedores al terminar.
