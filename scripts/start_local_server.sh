#!/bin/zsh
set -euo pipefail

# Ubica el servidor en la raiz del repositorio que contiene este script.
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# Puerto local reservado para este prototipo. Se evita el 8000 porque en este
# equipo ya esta ocupado por otro servicio.
export APP_HOST=127.0.0.1
export APP_PORT=8080

# Ejecuta el prototipo con el Python disponible en este equipo.
exec /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 src/app.py
