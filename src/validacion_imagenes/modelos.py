"""Esquemas Pydantic del servicio de validación de imágenes.

Reflejan los esquemas de `contratos/openapi-validacion-imagenes.yaml`.
"""

from typing import Literal

from pydantic import BaseModel


class ValidarImagenRequest(BaseModel):
    contenido_base64: str
    mime: str = "image/jpeg"
    nombre_archivo: str | None = None


class ValidarImagenResponse(BaseModel):
    veredicto: Literal["VALIDA", "INVALIDA"]
    motivo_codigo: (
        Literal[
            "ROSTRO_NO_VISIBLE",
            "DOCUMENTO_NO_VISIBLE",
            "SUPERPOSICION_DETECTADA",
            "IMAGEN_NO_INTERPRETABLE",
        ]
        | None
    ) = None
    motivo: str | None = None
    proveedor_llm: str | None = None
    tiempo_respuesta_ms: int | None = None


class Error(BaseModel):
    codigo: str
    mensaje: str
