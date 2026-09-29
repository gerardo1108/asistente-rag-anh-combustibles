"""Contrato estándar: lo que el asistente consume (`openapi-integracion.yaml`)."""

from fastapi import APIRouter, Depends, Header, Request, Response

from .almacen import Almacen
from .errores import ErrorAplicacion
from .modelos import EstadoSolicitud, SolicitudCreada, SolicitudRequest
from .seguridad import verificar_clave_asistente

router = APIRouter(tags=["Trámites"])


def obtener_almacen(request: Request) -> Almacen:
    return request.app.state.almacen


@router.post(
    "/v1/solicitudes",
    response_model=SolicitudCreada,
    status_code=201,
    dependencies=[Depends(verificar_clave_asistente)],
)
def registrar_solicitud(
    payload: SolicitudRequest,
    response: Response,
    almacen: Almacen = Depends(obtener_almacen),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if idempotency_key:
        existente = almacen.buscar_por_idempotency_key(idempotency_key)
        if existente is not None:
            response.status_code = 409
            return existente

    if not payload.declaracion_jurada:
        raise ErrorAplicacion(
            422,
            "DECLARACION_JURADA_REQUERIDA",
            "El registro concluye con la validación de los datos por parte del solicitante.",
        )

    return almacen.crear(payload, idempotency_key)


@router.get(
    "/v1/solicitudes/{codigo}/estado",
    response_model=EstadoSolicitud,
    dependencies=[Depends(verificar_clave_asistente)],
)
def consultar_estado_solicitud(codigo: str, almacen: Almacen = Depends(obtener_almacen)):
    estado = almacen.obtener_estado(codigo)
    if estado is None:
        raise ErrorAplicacion(
            404,
            "TRAMITE_NO_ENCONTRADO",
            "No se encontró un trámite con el código indicado.",
        )
    return estado
