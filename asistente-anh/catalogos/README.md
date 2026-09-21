# Catálogos

Datos de referencia usados por el formulario de registro (`src/chat/app.py`)
para poblar los selects de ubicación y actividad.

- `ubicaciones.json` — jerarquía Departamento → Provincia → Municipio, con un
  flag `es_frontera` por municipio.
- `actividades.json` — lista de actividades del solicitante.

## Limitaciones del dataset

**`ubicaciones.json` es un recorte reducido para el prototipo**, no la
división político-administrativa completa de Bolivia: cubre 3 de los 9
departamentos (La Paz, Cochabamba, Santa Cruz), con 5 provincias por
departamento y 5 municipios por provincia. No agregar entradas asumiendo que
el catálogo es exhaustivo.

**`es_frontera` es un proxy**, basado en cercanía geográfica real a un límite
internacional — no es la zonificación oficial que la ANH debe emitir según el
Decreto Supremo N° 5400 (Art. 16, Parágrafo III). A la fecha no se ha
identificado que esa zonificación oficial esté públicamente disponible. No
usar este flag como fuente de verdad normativa, solo como dato de referencia
para el prototipo.
