"""Instrumentación del prototipo (`openapi-utilidades-prototipo.yaml`)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from . import configuracion
from .almacen import Almacen
from .errores import ErrorAplicacion
from .modelos import ResultadoReinicio, Salud
from .rutas_verificacion import obtener_almacen

router = APIRouter(tags=["Utilidades"])


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@router.get("/health", response_model=Salud)
def verificar_salud(almacen: Almacen = Depends(obtener_almacen)):
    return Salud(registros=almacen.contar())


@router.post("/reiniciar", response_model=ResultadoReinicio)
def reiniciar_estado(request: Request, almacen: Almacen = Depends(obtener_almacen)):
    if not configuracion.permitir_reinicio():
        raise ErrorAplicacion(
            403,
            "REINICIO_NO_HABILITADO",
            "La operación de reinicio no está habilitada en esta instancia.",
        )
    eliminados = almacen.vaciar()
    cargados = almacen.cargar_semillas(request.app.state.ruta_semillas)
    return ResultadoReinicio(
        registros_eliminados=eliminados, registros_cargados=cargados, fecha=_ahora_iso()
    )
