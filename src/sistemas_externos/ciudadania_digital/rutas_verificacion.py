"""Verificación del titular (`openapi-ciudadania-digital.yaml`)."""

from fastapi import APIRouter, Depends, Request

from .almacen import Almacen
from .errores import ErrorAplicacion
from .modelos import Titular, VerificacionRequest
from .seguridad import verificar_clave_api

router = APIRouter(tags=["Ciudadanía Digital"])


def obtener_almacen(request: Request) -> Almacen:
    return request.app.state.almacen


@router.post(
    "/v1/verificacion-ciudadania",
    response_model=Titular,
    dependencies=[Depends(verificar_clave_api)],
)
def verificar_ciudadania(
    payload: VerificacionRequest, almacen: Almacen = Depends(obtener_almacen)
):
    if not payload.numero_documento.strip().isdigit():
        raise ErrorAplicacion(
            400,
            "DOCUMENTO_INVALIDO",
            "El número de documento no tiene un formato válido.",
        )

    fila = almacen.buscar(payload.numero_documento)
    if fila is None:
        raise ErrorAplicacion(
            404,
            "NO_REGISTRADO",
            "No existe un registro de Ciudadanía Digital para el documento indicado.",
        )

    if fila["estado_cuenta"] == "BLOQUEADA":
        raise ErrorAplicacion(
            409,
            "CUENTA_BLOQUEADA",
            "La cuenta de Ciudadanía Digital se encuentra bloqueada.",
        )
    if fila["estado_cuenta"] == "REQUIERE_REVALIDACION":
        raise ErrorAplicacion(
            409,
            "REQUIERE_REVALIDACION",
            "La cuenta de Ciudadanía Digital requiere revalidación.",
        )

    return Titular(
        tipo_documento=fila["tipo_documento"],
        numero_documento=fila["numero_documento"],
        nombres=fila["nombres"],
        primer_apellido=fila["primer_apellido"],
        segundo_apellido=fila["segundo_apellido"],
        fecha_nacimiento=fila["fecha_nacimiento"],
        genero=fila["genero"],
        correo=fila["correo"],
        celular=fila["celular"],
    )
