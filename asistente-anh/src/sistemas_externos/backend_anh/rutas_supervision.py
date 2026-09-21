"""Operaciones internas de la ANH (`openapi-supervision-anh.yaml`).

No forman parte del contrato estándar: son el caso de uso particular de esta
entidad para que el evaluador revise y resuelva solicitudes.
"""

from typing import Literal

from fastapi import APIRouter, Depends, Query

from .almacen import Almacen
from .errores import ErrorAplicacion
from .modelos import EstadoSolicitud, ListadoSolicitudes, ResolucionRequest, SolicitudDetalle
from .rutas_integracion import obtener_almacen
from .seguridad import verificar_clave_supervision

router = APIRouter(tags=["Supervisión"], dependencies=[Depends(verificar_clave_supervision)])

_ESTADOS_VALIDOS = {"REGISTRADO", "APROBADO", "RECHAZADO"}


@router.get("/v1/solicitudes", response_model=ListadoSolicitudes)
def listar_solicitudes(
    estado: Literal["REGISTRADO", "APROBADO", "RECHAZADO"] | None = None,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, description="Búsqueda por nombre o número de documento."),
    almacen: Almacen = Depends(obtener_almacen),
):
    total, solicitudes = almacen.listar(estado, pagina, por_pagina, q)
    return ListadoSolicitudes(
        total=total, pagina=pagina, por_pagina=por_pagina, solicitudes=solicitudes
    )


@router.get("/v1/solicitudes/{codigo}", response_model=SolicitudDetalle)
def obtener_solicitud(codigo: str, almacen: Almacen = Depends(obtener_almacen)):
    detalle = almacen.obtener_detalle(codigo)
    if detalle is None:
        raise ErrorAplicacion(
            404,
            "TRAMITE_NO_ENCONTRADO",
            "No se encontró un trámite con el código indicado.",
        )
    return detalle


@router.patch("/v1/solicitudes/{codigo}/estado", response_model=EstadoSolicitud)
def resolver_solicitud(
    codigo: str, payload: ResolucionRequest, almacen: Almacen = Depends(obtener_almacen)
):
    if payload.estado == "RECHAZADO" and not payload.motivo_rechazo:
        raise ErrorAplicacion(
            422,
            "MOTIVO_RECHAZO_REQUERIDO",
            "El rechazo de una solicitud requiere indicar el motivo.",
        )
    motivo = payload.motivo_rechazo if payload.estado == "RECHAZADO" else None
    return almacen.resolver(codigo, payload.estado, motivo)
