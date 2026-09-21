"""Esquemas Pydantic del Backend ANH.

Reflejan los esquemas de `contratos/openapi-integracion.yaml` y
`contratos/openapi-supervision-anh.yaml`, que declaran las mismas formas
(`Solicitante`, `CampoFormulario`, `Adjunto`, `EstadoSolicitud`, `Error`) por
separado. Aquí se definen una sola vez porque ambos contratos los implementa
el mismo servicio, sobre los mismos datos.
"""

from typing import Union

from pydantic import BaseModel, Field


class Solicitante(BaseModel):
    tipo_documento: str
    numero_documento: str
    nombres: str
    primer_apellido: str
    segundo_apellido: str | None = None
    correo: str | None = None
    celular: str | None = None

    def nombre_completo(self) -> str:
        partes = [self.nombres, self.primer_apellido, self.segundo_apellido]
        return " ".join(p for p in partes if p)


class CampoFormulario(BaseModel):
    campo: str
    indice: int | None = Field(default=None, ge=1)
    valor: Union[bool, int, float, str]


class Adjunto(BaseModel):
    tipo: str
    nombre_archivo: str
    mime: str = "image/jpeg"
    contenido_base64: str


class SolicitudRequest(BaseModel):
    tramite: str
    version_formulario: str
    canal_origen: str = "ASISTENTE_CONVERSACIONAL"
    solicitante: Solicitante
    datos: list[CampoFormulario] = Field(min_length=1)
    adjuntos: list[Adjunto] = Field(min_length=1)
    declaracion_jurada: bool


class SolicitudCreada(BaseModel):
    codigo_tramite: str
    estado: str = "REGISTRADO"
    fecha_registro: str


class EstadoSolicitud(BaseModel):
    codigo_tramite: str
    tramite: str
    estado: str
    fecha_registro: str
    fecha_resolucion: str | None = None
    motivo_rechazo: str | None = None


class ResumenSolicitud(BaseModel):
    codigo_tramite: str
    tramite: str
    solicitante: str
    numero_documento: str
    estado: str
    fecha_registro: str


class ListadoSolicitudes(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    solicitudes: list[ResumenSolicitud]


class SolicitudDetalle(BaseModel):
    codigo_tramite: str
    tramite: str
    version_formulario: str
    canal_origen: str
    solicitante: Solicitante
    datos: list[CampoFormulario]
    adjuntos: list[Adjunto]
    declaracion_jurada: bool
    estado: str
    fecha_registro: str
    fecha_resolucion: str | None = None
    motivo_rechazo: str | None = None


class ResolucionRequest(BaseModel):
    estado: str
    motivo_rechazo: str | None = None


class Error(BaseModel):
    codigo: str
    mensaje: str
    detalles: list[str] | None = None


class Salud(BaseModel):
    estado: str = "ok"
    servicio: str = "backend-anh"
    modo: str = "mock"
    persistencia: str = "sqlite"
    registros: int


class ResultadoReinicio(BaseModel):
    estado: str = "reiniciado"
    registros_eliminados: int
    registros_cargados: int
    fecha: str
