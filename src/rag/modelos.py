"""Esquemas Pydantic del servicio RAG.

Reflejan los esquemas de `contratos/openapi-rag.yaml`.
"""

from typing import Literal

from pydantic import BaseModel


class ConsultaRagRequest(BaseModel):
    pregunta: str
    contexto_conversacion: str | None = None


class Fuente(BaseModel):
    norma: str
    articulo: str
    fragmento: str | None = None


class ConsultaRagResponse(BaseModel):
    respuesta: str
    fuentes: list[Fuente]
    encontrado: bool
    proveedor_llm: str | None = None
    tiempo_respuesta_ms: int | None = None
    nota: str | None = None
    advertencia: str | None = None


class GenerarTextoEstadoRequest(BaseModel):
    codigo: str
    estado: Literal["REGISTRADO", "APROBADO", "RECHAZADO"]
    fecha_registro: str
    motivo_rechazo: str | None = None


class GenerarTextoEstadoResponse(BaseModel):
    texto: str


class Error(BaseModel):
    mensaje: str
