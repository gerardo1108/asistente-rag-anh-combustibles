# Semillas

Datos iniciales que los servicios simulados cargan al arrancar.

- `solicitudes.json` — trámites de ejemplo en distintos estados
- `titulares.json` — personas registradas en Ciudadanía Digital
- `imagenes/` — fotografías referenciadas por nombre desde `solicitudes.json`

Las imágenes van como archivos sueltos, no incrustadas en base64 dentro del
JSON: así el archivo queda legible y revisable en Git. El servicio las lee al
arrancar y las codifica.

Redimensionar a ~800 px de ancho antes de usarlas.

Casos a cubrir: trámite aprobado, rechazado con motivo, pendiente de
evaluación, persona sin Ciudadanía Digital, persona que requiere revalidación.
