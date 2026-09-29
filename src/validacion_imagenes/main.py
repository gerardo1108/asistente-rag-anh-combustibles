"""Servicio de validación de imágenes: verifica que la foto muestre rostro y cédula."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import rutas_validacion, validador_core
from .errores import ErrorAplicacion
from .modelos import Error

logging.basicConfig(level=logging.INFO)

MENSAJE_SOLICITUD_INVALIDA = "El cuerpo de la solicitud no cumple con la estructura requerida."


def crear_app(motor: validador_core.MotorValidacion | None = None) -> FastAPI:
    app = FastAPI(title="Validación de Imágenes - Asistente ANH", version="1.0.0")
    # Prototipo local: cualquier origen puede llamar. No hay cookies/sesión
    # ni auth en este servicio, así que no hace falta allow_credentials.
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    app.state.motor = motor or validador_core.cargar_motor()

    app.include_router(rutas_validacion.router)

    @app.exception_handler(ErrorAplicacion)
    async def manejar_error_aplicacion(request: Request, exc: ErrorAplicacion):
        cuerpo = Error(codigo=exc.codigo, mensaje=exc.mensaje)
        return JSONResponse(status_code=exc.status_code, content=cuerpo.model_dump())

    @app.exception_handler(RequestValidationError)
    async def manejar_error_validacion(request: Request, exc: RequestValidationError):
        cuerpo = Error(codigo="SOLICITUD_INVALIDA", mensaje=MENSAJE_SOLICITUD_INVALIDA)
        return JSONResponse(status_code=400, content=cuerpo.model_dump())

    return app


app = crear_app()
