"""Evaluación de la foto (rostro + cédula) con un LLM de visión.

Sigue el mismo patrón de fallback/reintentos que `rag/rag_core.py`, pero
acotado a proveedores con capacidad de visión confirmada: hoy solo Gemini
(`google-genai`). El mecanismo de lista de proveedores (`configuracion.
proveedores_vision()`) queda igual de extensible por si en el futuro se
confirma un modelo de Groq con visión estable, pero no se implementa ese
fallback ahora — sería trabajo especulativo sobre una API no verificada.

Este servicio solo verifica presencia y oclusión (¿hay un rostro?, ¿hay una
cédula?, ¿algo los tapa?). No evalúa legibilidad fina, vigencia del
documento, ni que el rostro corresponda a la persona registrada en
Ciudadanía Digital — eso sigue siendo responsabilidad del evaluador humano.
"""

import base64
import binascii
import io
import logging
import time
from dataclasses import dataclass

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ValidationError

from . import configuracion
from .modelos import ValidarImagenResponse

INSTRUCCIONES_SISTEMA = """
Eres un verificador automático de fotografías para un trámite de la ANH (Bolivia).

Cada foto debe mostrar a una persona sosteniendo su cédula de identidad.
Evalúa ÚNICAMENTE estos tres aspectos:

1. rostro_visible: ¿se distingue con claridad un rostro humano en la imagen?
2. documento_visible: ¿se distingue con claridad una cédula de identidad (u
   otro documento de identidad similar) sostenida por la persona?
3. hay_superposicion: ¿algo tapa parcial o totalmente el rostro o el
   documento (dedos, reflejos, otros objetos, recortes del encuadre, o
   desenfoque severo que impida verlos)?

No evalúes legibilidad fina del número de documento, vigencia, ni si la
persona es quien dice ser: eso no es tu tarea.

Responde SIEMPRE en el formato JSON solicitado. El campo "motivo" es una
frase breve en español, para mostrar al ciudadano, que explique el resultado
(por ejemplo: "Rostro y documento visibles, sin obstrucciones." o "No se
distingue ninguna cédula de identidad en la foto.").
"""

_BACKOFF_BASE_SEGUNDOS = 1.0  # 1s, 2s, 4s

_LADO_MAXIMO_PX = 1024

_logger = logging.getLogger(__name__)


class ImagenInvalida(ValueError):
    pass


class ImagenDemasiadoGrande(ValueError):
    pass


class ErrorGeneracion(Exception):
    pass


class RespuestaNoInterpretable(Exception):
    """El proveedor respondió, pero no en un formato utilizable (JSON malformado
    o campos inconsistentes). Distinto de un error de conexión/servicio: se
    trata como abstención (`IMAGEN_NO_INTERPRETABLE`), no como falla 500."""


class VeredictoLLM(BaseModel):
    rostro_visible: bool
    documento_visible: bool
    hay_superposicion: bool
    motivo: str


@dataclass
class MotorValidacion:
    clientes: dict[str, object]
    modelos: dict[str, str]
    proveedores: list[str]


def cargar_motor() -> MotorValidacion:
    proveedores = configuracion.proveedores_vision()
    clientes: dict[str, object] = {}
    modelos: dict[str, str] = {}

    if "gemini" in proveedores:
        clientes["gemini"] = genai.Client(api_key=configuracion.google_api_key())
        modelos["gemini"] = configuracion.modelo_gemini()

    return MotorValidacion(clientes=clientes, modelos=modelos, proveedores=proveedores)


def decodificar_y_validar_imagen(contenido_base64: str) -> bytes:
    try:
        datos = base64.b64decode(contenido_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ImagenInvalida("El contenido no corresponde a una imagen válida.") from exc

    if len(datos) > configuracion.max_bytes_imagen():
        raise ImagenDemasiadoGrande("La imagen supera el tamaño máximo permitido.")

    try:
        imagen = Image.open(io.BytesIO(datos))
        imagen.verify()
    except (UnidentifiedImageError, Exception) as exc:
        raise ImagenInvalida("El contenido no corresponde a una imagen válida.") from exc

    return datos


def _redimensionar(datos: bytes) -> bytes:
    imagen = Image.open(io.BytesIO(datos)).convert("RGB")
    ancho, alto = imagen.size
    lado_mayor = max(ancho, alto)
    if lado_mayor > _LADO_MAXIMO_PX:
        factor = _LADO_MAXIMO_PX / lado_mayor
        imagen = imagen.resize((round(ancho * factor), round(alto * factor)))
    salida = io.BytesIO()
    imagen.save(salida, format="JPEG", quality=85)
    return salida.getvalue()


def _generar_con_gemini(motor: MotorValidacion, imagen_bytes: bytes) -> VeredictoLLM:
    respuesta = motor.clientes["gemini"].models.generate_content(
        model=motor.modelos["gemini"],
        contents=[
            genai_types.Part.from_bytes(data=imagen_bytes, mime_type="image/jpeg"),
            "Evalúa esta fotografía según las reglas del system prompt.",
        ],
        config=genai_types.GenerateContentConfig(
            system_instruction=INSTRUCCIONES_SISTEMA,
            max_output_tokens=300,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=VeredictoLLM,
            # No se declaran tools/functions, así que AFC no aplica; se
            # desactiva para no arrastrar el aviso del SDK en cada llamada.
            automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    if respuesta.parsed is not None:
        return respuesta.parsed
    try:
        return VeredictoLLM.model_validate_json((respuesta.text or "").strip())
    except ValidationError as exc:
        raise RespuestaNoInterpretable("El modelo no devolvió un JSON interpretable.") from exc


_GENERADORES = {"gemini": _generar_con_gemini}

# Errores transitorios (saturación del servidor, límite de tasa, timeout,
# conexión): tiene sentido reintentar. RespuestaNoInterpretable también se
# reintenta (el modelo puede devolver JSON malformado en un intento aislado
# y uno válido en el siguiente).
_ERRORES_TRANSITORIOS = {
    "gemini": (genai_errors.ServerError, ConnectionError, TimeoutError, RespuestaNoInterpretable),
}


@dataclass
class ResultadoValidacion:
    veredicto_llm: VeredictoLLM
    proveedor: str
    tiempo_ms: int


def _intentar_proveedor(motor: MotorValidacion, proveedor: str, imagen_bytes: bytes) -> ResultadoValidacion:
    generador = _GENERADORES[proveedor]
    errores_transitorios = _ERRORES_TRANSITORIOS[proveedor]

    ultimo_error: Exception
    max_intentos = configuracion.reintentos_por_proveedor()
    for intento in range(1, max_intentos + 1):
        try:
            inicio = time.monotonic()
            veredicto = generador(motor, imagen_bytes)
            tiempo_ms = round((time.monotonic() - inicio) * 1000)
            return ResultadoValidacion(veredicto_llm=veredicto, proveedor=proveedor, tiempo_ms=tiempo_ms)
        except Exception as exc:
            ultimo_error = exc
            transitorio = isinstance(exc, errores_transitorios)
            _logger.warning(
                "Intento %d/%d con %s falló (%s): %s",
                intento,
                max_intentos,
                proveedor,
                "transitorio" if transitorio else "no transitorio, no se reintenta",
                exc,
            )
            if not transitorio or intento == max_intentos:
                break
            time.sleep(_BACKOFF_BASE_SEGUNDOS * (2 ** (intento - 1)))

    raise ultimo_error


def _intentar_todos_los_proveedores(motor: MotorValidacion, imagen_bytes: bytes) -> ResultadoValidacion:
    """Prueba los proveedores de `motor.proveedores` en orden; agota los reintentos
    de cada uno (`_intentar_proveedor`) antes de pasar al siguiente."""
    ultimo_error: Exception | None = None
    for proveedor in motor.proveedores:
        try:
            return _intentar_proveedor(motor, proveedor, imagen_bytes)
        except Exception as exc:
            ultimo_error = exc
            _logger.warning("Proveedor %s falló, se prueba el siguiente: %s", proveedor, exc)

    _logger.error("Todos los proveedores de visión fallaron: %s", motor.proveedores)
    if isinstance(ultimo_error, RespuestaNoInterpretable):
        raise ultimo_error
    raise ErrorGeneracion("El servicio de validación no respondió correctamente.")


def _mapear_veredicto(resultado: ResultadoValidacion) -> ValidarImagenResponse:
    v = resultado.veredicto_llm
    if v.rostro_visible and v.documento_visible and not v.hay_superposicion:
        return ValidarImagenResponse(
            veredicto="VALIDA",
            proveedor_llm=resultado.proveedor,
            tiempo_respuesta_ms=resultado.tiempo_ms,
        )

    if not v.rostro_visible:
        motivo_codigo = "ROSTRO_NO_VISIBLE"
    elif not v.documento_visible:
        motivo_codigo = "DOCUMENTO_NO_VISIBLE"
    else:
        motivo_codigo = "SUPERPOSICION_DETECTADA"

    return ValidarImagenResponse(
        veredicto="INVALIDA",
        motivo_codigo=motivo_codigo,
        motivo=v.motivo,
        proveedor_llm=resultado.proveedor,
        tiempo_respuesta_ms=resultado.tiempo_ms,
    )


def validar(motor: MotorValidacion, contenido_base64: str) -> ValidarImagenResponse:
    datos = decodificar_y_validar_imagen(contenido_base64)
    imagen_bytes = _redimensionar(datos)

    try:
        resultado = _intentar_todos_los_proveedores(motor, imagen_bytes)
    except RespuestaNoInterpretable:
        return ValidarImagenResponse(
            veredicto="INVALIDA",
            motivo_codigo="IMAGEN_NO_INTERPRETABLE",
            motivo="La imagen está demasiado oscura, borrosa, o no permite evaluarla.",
        )

    return _mapear_veredicto(resultado)
