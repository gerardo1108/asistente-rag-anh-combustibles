"""Configuración de Ciudadanía Digital, leída de variables de entorno."""

import os
from pathlib import Path

# ciudadania_digital/ -> sistemas_externos/ -> src/ -> raíz del proyecto
RAIZ_PROYECTO = Path(__file__).resolve().parents[3]


def permitir_reinicio() -> bool:
    valor = os.environ.get("PERMITIR_REINICIO", "")
    return valor.strip().lower() in {"1", "true", "si", "sí"}


def ruta_base_datos() -> Path:
    return Path(os.environ.get("CD_DB_PATH", "ciudadania_digital.db"))


def ruta_semillas() -> Path:
    return Path(
        os.environ.get(
            "CD_RUTA_SEMILLAS", str(RAIZ_PROYECTO / "semillas" / "titulares.json")
        )
    )
