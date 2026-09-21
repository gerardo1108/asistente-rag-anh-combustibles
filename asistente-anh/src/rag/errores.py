"""Errores de aplicación: llevan el status HTTP y mensaje que va en la respuesta.

El esquema `Error` de `openapi-rag.yaml` solo tiene `mensaje` (a diferencia
del de `backend_anh`, que además lleva `codigo` y `detalles`).
"""


class ErrorAplicacion(Exception):
    def __init__(self, status_code: int, mensaje: str):
        super().__init__(mensaje)
        self.status_code = status_code
        self.mensaje = mensaje
