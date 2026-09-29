"""Verificación de la clave de API.

Dos claves distintas por diseño: `AsistenteApiKey` habilita el contrato
estándar, `SupervisionApiKey` las operaciones internas. El asistente no puede
resolver trámites; la supervisión no registra solicitudes. En el prototipo el
mock acepta cualquier valor no vacío: la clave se declara para dejar
establecido el punto de integración y la separación de permisos, no para
ejercer control real durante el piloto.
"""

from fastapi import Header

from .errores import ErrorAplicacion

_MENSAJE_NO_AUTORIZADO = "La clave de API es inválida o no fue proporcionada."


def _verificar(x_api_key: str | None) -> str:
    if not x_api_key or not x_api_key.strip():
        raise ErrorAplicacion(401, "NO_AUTORIZADO", _MENSAJE_NO_AUTORIZADO)
    return x_api_key


async def verificar_clave_asistente(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    return _verificar(x_api_key)


async def verificar_clave_supervision(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    return _verificar(x_api_key)
