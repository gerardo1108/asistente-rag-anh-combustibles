"""Texto de respuesta de 'Ver estado', generado por LLM (`openapi-rag.yaml`).

No forma parte de la consulta al corpus normativo (`rutas_consultas.py`):
toma datos ya estructurados de un trámite y los redacta para el ciudadano.
Reusa la infraestructura de proveedores/fallback de `rag_core.py`.
"""

from fastapi import APIRouter, Request

from . import rag_core
from .modelos import GenerarTextoEstadoRequest, GenerarTextoEstadoResponse

router = APIRouter(tags=["Generación de texto"])

_DESCRIPCION_FALLBACK = {
    "REGISTRADO": "está pendiente de evaluación",
    "APROBADO": "fue aprobado",
    "RECHAZADO": "fue rechazado",
}


def _escapar(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _texto_fallback(payload: GenerarTextoEstadoRequest) -> str:
    """Mensaje de respaldo si el LLM no responde: mismos datos, mismo
    formato (<strong> en código/estado) que se espera del LLM, para que el
    frontend lo renderice igual."""
    descripcion = _DESCRIPCION_FALLBACK[payload.estado]
    texto = f"El trámite <strong>{_escapar(payload.codigo)}</strong> <strong>{payload.estado}</strong> {descripcion}."
    if payload.estado == "RECHAZADO" and payload.motivo_rechazo:
        texto += f" Motivo: {_escapar(payload.motivo_rechazo)}."
    return texto


@router.post("/v1/generar-texto-estado", response_model=GenerarTextoEstadoResponse)
def generar(payload: GenerarTextoEstadoRequest, request: Request):
    motor: rag_core.MotorRag = request.app.state.motor
    datos = payload.model_dump(exclude_none=True)
    try:
        resultado = rag_core.generar_texto_estado(motor, datos)
        return GenerarTextoEstadoResponse(texto=resultado.texto)
    except rag_core.ErrorGeneracion:
        # El llamador nunca debe ver una falla del LLM como error: se
        # responde 200 con un texto de respaldo armado con los mismos datos.
        return GenerarTextoEstadoResponse(texto=_texto_fallback(payload))
