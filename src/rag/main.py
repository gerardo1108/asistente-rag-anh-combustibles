"""Servicio de Consultas RAG: motor de recuperación aumentada sobre el corpus normativo."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import rag_core, rutas_consultas, rutas_generar_estado
from .errores import ErrorAplicacion
from .modelos import Error

# Sin esto, los `logger.info(...)` del paquete (ej. cuando se activa el
# fallback de reformulación de pregunta en rag_core.py) se descartan en
# silencio: sin ningún handler configurado, Python solo emite WARNING o más
# grave por default.
logging.basicConfig(level=logging.INFO)

MENSAJE_SOLICITUD_INVALIDA = "El cuerpo de la solicitud no cumple con la estructura requerida."


def crear_app(motor: rag_core.MotorRag | None = None) -> FastAPI:
    app = FastAPI(title="Consultas RAG - Asistente ANH", version="1.0.0")
    # Prototipo local: cualquier origen puede llamar. No hay cookies/sesión
    # ni auth en este servicio, así que no hace falta allow_credentials.
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    app.state.motor = motor or rag_core.cargar_motor()

    app.include_router(rutas_consultas.router)
    app.include_router(rutas_generar_estado.router)

    @app.exception_handler(ErrorAplicacion)
    async def manejar_error_aplicacion(request: Request, exc: ErrorAplicacion):
        return JSONResponse(
            status_code=exc.status_code, content=Error(mensaje=exc.mensaje).model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def manejar_error_validacion(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=400, content=Error(mensaje=MENSAJE_SOLICITUD_INVALIDA).model_dump())

    return app


app = crear_app()
