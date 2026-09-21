"""Verificación de la clave de API.

Una sola clave para este servicio: identifica al asistente ante Ciudadanía
Digital. En el prototipo el mock acepta cualquier valor no vacío; la clave se
declara para dejar establecido el punto de integración, no para ejercer
control real durante el piloto.
"""

from fastapi import Header

from .errores import ErrorAplicacion


async def verificar_clave_api(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    if not x_api_key or not x_api_key.strip():
        raise ErrorAplicacion(
            401, "NO_AUTORIZADO", "La clave de API es inválida o no fue proporcionada."
        )
    return x_api_key
