"""Errores de aplicación: llevan el código y mensaje que va en la respuesta."""


class ErrorAplicacion(Exception):
    def __init__(
        self,
        status_code: int,
        codigo: str,
        mensaje: str,
        detalles: list[str] | None = None,
    ):
        super().__init__(mensaje)
        self.status_code = status_code
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalles = detalles
