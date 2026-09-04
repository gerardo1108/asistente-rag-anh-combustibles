#!/bin/zsh
set -euo pipefail

# Ubica siempre el servidor en la raiz del repositorio, aunque macOS lo
# ejecute desde otro directorio durante el inicio de sesion.
cd /Users/gerardoqinterosandoval/Documents/asistente-rag-anh-combustibles/repo-prototipo

# Puerto local reservado para este prototipo. Se evita el 8000 porque en este
# equipo ya esta ocupado por otro servicio.
export APP_HOST=127.0.0.1
export APP_PORT=8001

# Ejecuta el prototipo con el Python disponible en este equipo.
exec /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 src/app.py
