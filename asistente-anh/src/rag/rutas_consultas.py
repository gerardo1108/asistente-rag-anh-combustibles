"""Consulta al motor RAG (`openapi-rag.yaml`)."""

from fastapi import APIRouter, Request

from . import rag_core
from .errores import ErrorAplicacion
from .modelos import ConsultaRagRequest, ConsultaRagResponse

router = APIRouter(tags=["Consultas"])


@router.post("/v1/consultas-rag", response_model=ConsultaRagResponse)
def consultar(payload: ConsultaRagRequest, request: Request):
    if not payload.pregunta.strip():
        raise ErrorAplicacion(400, "La pregunta no puede estar vacía.")

    motor: rag_core.MotorRag = request.app.state.motor
    try:
        return rag_core.responder(motor, payload.pregunta, payload.contexto_conversacion)
    except rag_core.ErrorGeneracion as exc:
        raise ErrorAplicacion(500, str(exc)) from exc
