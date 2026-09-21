"""Configuración del Backend ANH, leída de variables de entorno."""

import os
from pathlib import Path

# backend_anh/ -> sistemas_externos/ -> src/ -> raíz del proyecto
RAIZ_PROYECTO = Path(__file__).resolve().parents[3]


def permitir_reinicio() -> bool:
    valor = os.environ.get("PERMITIR_REINICIO", "")
    return valor.strip().lower() in {"1", "true", "si", "sí"}


def ruta_base_datos() -> Path:
    return Path(os.environ.get("ANH_DB_PATH", "backend_anh.db"))


def ruta_semillas() -> Path:
    return Path(
        os.environ.get(
            "ANH_RUTA_SEMILLAS", str(RAIZ_PROYECTO / "semillas" / "solicitudes.json")
        )
    )


def ruta_imagenes() -> Path:
    return Path(
        os.environ.get("ANH_RUTA_IMAGENES", str(RAIZ_PROYECTO / "semillas" / "imagenes"))
    )
