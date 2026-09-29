"""Validación de la foto (`openapi-validacion-imagenes.yaml`)."""

from fastapi import APIRouter, Request

from . import configuracion, validador_core
from .errores import ErrorAplicacion
from .modelos import ValidarImagenRequest, ValidarImagenResponse

router = APIRouter(tags=["Validación de imágenes"])


@router.post("/v1/validaciones-imagen", response_model=ValidarImagenResponse)
def validar_imagen(payload: ValidarImagenRequest, request: Request):
    if payload.mime not in configuracion.MIMES_SOPORTADOS:
        raise ErrorAplicacion(400, "MIME_NO_SOPORTADO", "Formato no soportado. Usá JPG o PNG.")

    motor: validador_core.MotorValidacion = request.app.state.motor
    try:
        return validador_core.validar(motor, payload.contenido_base64)
    except validador_core.ImagenDemasiadoGrande as exc:
        raise ErrorAplicacion(400, "IMAGEN_DEMASIADO_GRANDE", str(exc)) from exc
    except validador_core.ImagenInvalida as exc:
        raise ErrorAplicacion(400, "IMAGEN_INVALIDA", str(exc)) from exc
    except validador_core.ErrorGeneracion as exc:
        raise ErrorAplicacion(500, "SERVICIO_VISION_NO_DISPONIBLE", str(exc)) from exc
