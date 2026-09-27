"""Configuración del servicio de validación de imágenes, leída de variables de entorno."""

import os

from dotenv import load_dotenv

load_dotenv()

MENSAJE_API_KEY_FALTANTE = (
    "Falta la variable de entorno GOOGLE_API_KEY. Conseguí una clave gratuita "
    "en https://aistudio.google.com/apikey."
)

# Hoy solo "gemini" tiene un modelo de visión confirmado. El mecanismo queda
# igual de extensible que `proveedores_llm()` de rag/configuracion.py por si
# en el futuro se confirma un modelo de Groq con visión estable.
PROVEEDORES_VALIDOS = {"gemini"}

MIMES_SOPORTADOS = {"image/jpeg", "image/png"}


def activa() -> bool:
    return os.environ.get("VALIDACION_IMAGENES_ACTIVA", "false").strip().lower() in {
        "1", "true", "si", "sí", "yes"
    }


def reintentos_por_proveedor() -> int:
    return max(1, int(os.environ.get("VALIDACION_IMAGENES_REINTENTOS", "1")))


def google_api_key() -> str:
    clave = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not clave:
        raise RuntimeError(MENSAJE_API_KEY_FALTANTE)
    return clave


def modelo_gemini() -> str:
    return os.environ.get("VALIDACION_IMAGENES_MODELO_GEMINI", "gemini-3.1-flash-lite")


def proveedores_vision() -> list[str]:
    valor = os.environ.get("VALIDACION_IMAGENES_PROVEEDORES", "gemini")
    proveedores = [p.strip().lower() for p in valor.split(",") if p.strip()]
    if not proveedores:
        raise RuntimeError("VALIDACION_IMAGENES_PROVEEDORES no puede quedar vacío.")
    desconocidos = sorted(set(proveedores) - PROVEEDORES_VALIDOS)
    if desconocidos:
        raise RuntimeError(
            f"VALIDACION_IMAGENES_PROVEEDORES tiene proveedores desconocidos: {desconocidos}. "
            f"Válidos: {sorted(PROVEEDORES_VALIDOS)}."
        )
    return proveedores


def max_bytes_imagen() -> int:
    return int(os.environ.get("VALIDACION_IMAGENES_MAX_BYTES", str(8 * 1024 * 1024)))
