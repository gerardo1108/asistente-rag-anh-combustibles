"""Esquemas Pydantic de Ciudadanía Digital, según `openapi-ciudadania-digital.yaml`."""


from pydantic import BaseModel


class VerificacionRequest(BaseModel):
    tipo_documento: str = "CI"
    numero_documento: str


class Titular(BaseModel):
    tipo_documento: str
    numero_documento: str
    nombres: str
    primer_apellido: str
    segundo_apellido: str | None = None
    fecha_nacimiento: str
    genero: str | None = None
    correo: str | None = None
    celular: str | None = None


class Error(BaseModel):
    codigo: str
    mensaje: str
    detalles: list[str] | None = None


class Salud(BaseModel):
    estado: str = "ok"
    servicio: str = "ciudadania-digital"
    modo: str = "mock"
    persistencia: str = "sqlite"
    registros: int


class ResultadoReinicio(BaseModel):
    estado: str = "reiniciado"
    registros_eliminados: int
    registros_cargados: int
    fecha: str
