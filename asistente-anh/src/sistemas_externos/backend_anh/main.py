"""Backend ANH (mock): registro de solicitudes, supervisión y utilidades."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import configuracion, rutas_integracion, rutas_supervision, rutas_utilidades
from .almacen import Almacen
from .errores import ErrorAplicacion
from .modelos import Error


def crear_app(
    almacen: Almacen | None = None,
    ruta_semillas: Path | None = None,
    ruta_imagenes: Path | None = None,
) -> FastAPI:
    app = FastAPI(title="Backend ANH (mock)", version="1.0.0")
    # Prototipo local: cualquier origen puede llamar. No hay cookies/sesión
    # (la auth es el header X-API-Key), así que no hace falta allow_credentials.
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    app.state.ruta_semillas = ruta_semillas or configuracion.ruta_semillas()
    app.state.ruta_imagenes = ruta_imagenes or configuracion.ruta_imagenes()
    app.state.almacen = almacen or Almacen(configuracion.ruta_base_datos())
    app.state.almacen.inicializar_si_vacio(
        app.state.ruta_semillas, app.state.ruta_imagenes
    )

    app.include_router(rutas_integracion.router)
    app.include_router(rutas_supervision.router)
    app.include_router(rutas_utilidades.router)

    @app.exception_handler(ErrorAplicacion)
    async def manejar_error_aplicacion(request: Request, exc: ErrorAplicacion):
        cuerpo = Error(codigo=exc.codigo, mensaje=exc.mensaje, detalles=exc.detalles)
        return JSONResponse(
            status_code=exc.status_code, content=cuerpo.model_dump(exclude_none=True)
        )

    @app.exception_handler(RequestValidationError)
    async def manejar_error_validacion(request: Request, exc: RequestValidationError):
        errores = exc.errors()
        if any(e.get("type") == "json_invalid" for e in errores):
            cuerpo = Error(
                codigo="SOLICITUD_MALFORMADA",
                mensaje="El cuerpo de la petición no es un JSON válido.",
            )
            return JSONResponse(status_code=400, content=cuerpo.model_dump(exclude_none=True))

        detalles = [
            ".".join(str(p) for p in e["loc"] if p != "body") for e in errores
        ]
        cuerpo = Error(
            codigo="SOLICITUD_INVALIDA",
            mensaje="El cuerpo de la solicitud no cumple con la estructura requerida.",
            detalles=detalles,
        )
        return JSONResponse(status_code=422, content=cuerpo.model_dump(exclude_none=True))

    return app


app = crear_app()
