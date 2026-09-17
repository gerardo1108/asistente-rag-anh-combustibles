"""Acceso configurable al backend local o a los servicios HTTP simulados."""

import base64
import json
import os
import uuid
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import backend_simulado


class BackendIntegrationError(RuntimeError):
    """Error controlado al comunicarse con los servicios externos."""


def get_backend_mode() -> str:
    """Devuelve el modo de integracion activo."""

    return os.environ.get("BACKEND_MODE", "local").lower().strip()


def verificar_ciudadania_digital(ci: str) -> dict:
    """Verifica una identidad usando el proveedor configurado."""

    if get_backend_mode() != "http":
        result = backend_simulado.verificar_ciudadania_digital(ci)
        if result.get("registrado"):
            partes = result["nombre"].split()
            result["solicitante"] = {
                "tipo_documento": "CI",
                "numero_documento": result["ci"],
                "nombres": " ".join(partes[:-2]) or partes[0],
                "primer_apellido": partes[-2] if len(partes) > 1 else "Sin apellido",
                "segundo_apellido": partes[-1] if len(partes) > 2 else None,
            }
        return result

    try:
        titular = _request_json(
            "POST",
            f"{_ciudadania_url()}/v1/verificacion-ciudadania",
            {"tipo_documento": "CI", "numero_documento": ci.strip()},
        )
    except BackendIntegrationError as exc:
        return {"registrado": False, "mensaje": str(exc)}

    nombre = " ".join(
        value
        for value in (
            titular.get("nombres"),
            titular.get("primer_apellido"),
            titular.get("segundo_apellido"),
        )
        if value
    )
    return {
        "registrado": True,
        "ci": titular["numero_documento"],
        "nombre": nombre,
        "solicitante": titular,
    }


def validar_volumen(zona: str, volumen_litros: int) -> tuple[bool, str]:
    """Mantiene la regla de negocio en el orquestador."""

    return backend_simulado.validar_volumen(zona, volumen_litros)


def crear_solicitud(datos: dict):
    """Registra una solicitud localmente o mediante el contrato HTTP."""

    if get_backend_mode() != "http":
        return backend_simulado.crear_solicitud(datos)

    solicitante = dict(datos.get("solicitante") or {})
    solicitante.setdefault("tipo_documento", "CI")
    solicitante.setdefault("numero_documento", datos["ci"])
    payload = {
        "tramite": "ANH-REGISTRO-CONSUMO-FUERA-TANQUE",
        "version_formulario": "1.0",
        "canal_origen": "ASISTENTE_CONVERSACIONAL",
        "solicitante": solicitante,
        "datos": [
            {"campo": "actividad", "valor": datos["actividad"]},
            {"campo": "zona", "valor": datos["zona"]},
            {"campo": "producto", "valor": datos["combustible"].upper()},
            {"campo": "volumen_litros", "valor": int(datos["volumen_litros"])},
            {"campo": "uso_destino", "valor": datos["destino"]},
        ],
        "adjuntos": [
            {
                "tipo": "FOTO_TITULAR_CON_CI",
                "nombre_archivo": "evidencia_simulada.jpg",
                "mime": "image/jpeg",
                "contenido_base64": base64.b64encode(
                    b"Evidencia simulada sin biometria real"
                ).decode("ascii"),
            }
        ],
        "declaracion_jurada": True,
    }
    response = _request_json(
        "POST",
        f"{_backend_url()}/v1/solicitudes",
        payload,
        {"Idempotency-Key": str(uuid.uuid4())},
    )
    return SimpleNamespace(codigo=response["codigo_tramite"])


def consultar_solicitud(codigo: str, ci: str | None = None) -> dict | None:
    """Consulta seguimiento y devuelve el formato esperado por la interfaz."""

    if get_backend_mode() != "http":
        return backend_simulado.consultar_solicitud(codigo, ci)

    try:
        response = _request_json(
            "GET",
            f"{_backend_url()}/v1/solicitudes/{quote(codigo.strip().upper())}/estado",
        )
    except BackendIntegrationError as exc:
        if "TRAMITE_NO_ENCONTRADO" in str(exc):
            return None
        raise
    return {
        "codigo": response["codigo_tramite"],
        "ci": ci or "",
        "nombre": "Titular verificado",
        "estado": _estado_a_interfaz(response["estado"]),
        "observacion": response.get("motivo_rechazo") or "Sin observaciones.",
        "creada_en": response.get("fecha_registro", ""),
    }


def listar_solicitudes() -> list[dict]:
    """Lista solicitudes para el panel evaluador."""

    if get_backend_mode() != "http":
        return backend_simulado.listar_solicitudes()

    listado = _request_json(
        "GET", f"{_backend_url()}/v1/solicitudes?{urlencode({'por_pagina': 100})}"
    )
    return [_obtener_detalle_http(item["codigo_tramite"]) for item in listado["solicitudes"]]


def actualizar_estado(codigo: str, estado: str, observacion: str = "") -> dict | None:
    """Resuelve una solicitud desde el panel local."""

    if get_backend_mode() != "http":
        return backend_simulado.actualizar_estado(codigo, estado, observacion)

    estado_api = {
        "aprobada": "APROBADO",
        "rechazada": "RECHAZADO",
        "pendiente": "REGISTRADO",
    }.get(estado.lower().strip())
    if estado_api == "REGISTRADO":
        raise BackendIntegrationError("El contrato HTTP no permite devolver un tramite a REGISTRADO.")
    payload = {"estado": estado_api}
    if estado_api == "RECHAZADO":
        payload["motivo_rechazo"] = observacion or "Solicitud rechazada durante la evaluacion simulada."
    response = _request_json(
        "PATCH",
        f"{_backend_url()}/v1/solicitudes/{quote(codigo.strip().upper())}/estado",
        payload,
    )
    return {
        "codigo": response["codigo_tramite"],
        "estado": _estado_a_interfaz(response["estado"]),
        "observacion": response.get("motivo_rechazo") or observacion,
    }


def _obtener_detalle_http(codigo: str) -> dict:
    detalle = _request_json(
        "GET", f"{_backend_url()}/v1/solicitudes/{quote(codigo)}"
    )
    campos = {item["campo"]: item["valor"] for item in detalle["datos"]}
    solicitante = detalle["solicitante"]
    nombre = " ".join(
        value
        for value in (
            solicitante.get("nombres"),
            solicitante.get("primer_apellido"),
            solicitante.get("segundo_apellido"),
        )
        if value
    )
    return {
        "codigo": detalle["codigo_tramite"],
        "ci": solicitante["numero_documento"],
        "nombre": nombre,
        "actividad": str(campos.get("actividad", "No declarada")),
        "zona": str(campos.get("zona", "No declarada")),
        "combustible": str(campos.get("producto", "No declarado")).lower(),
        "volumen_litros": campos.get("volumen_litros", "No declarado"),
        "destino": str(campos.get("uso_destino", "No declarado")),
        "foto_validada": bool(detalle.get("adjuntos")),
        "foto_validacion_metodo": "simulacion_controlada_sin_biometria",
        "foto_evidencia": "Adjunto recibido por contrato HTTP",
        "estado": _estado_a_interfaz(detalle["estado"]),
        "observacion": detalle.get("motivo_rechazo") or "Sin observaciones.",
        "creada_en": detalle.get("fecha_registro", ""),
    }


def _request_json(
    method: str, url: str, payload: dict | None = None, extra_headers: dict | None = None
) -> dict:
    headers = {"X-API-Key": os.environ.get("SERVICIOS_API_KEY", "demo-local")}
    headers.update(extra_headers or {})
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            error = json.loads(body)
            detail = error.get("detail", error)
            code = detail.get("codigo", "ERROR_HTTP") if isinstance(detail, dict) else "ERROR_HTTP"
            message = detail.get("mensaje", str(detail)) if isinstance(detail, dict) else str(detail)
        except json.JSONDecodeError:
            code, message = "ERROR_HTTP", body or str(exc)
        raise BackendIntegrationError(f"{code}: {message}") from exc
    except (URLError, TimeoutError) as exc:
        raise BackendIntegrationError(
            "El servicio simulado no esta disponible. Verifica que Docker Compose este activo."
        ) from exc


def _backend_url() -> str:
    return os.environ.get("BACKEND_ANH_URL", "http://localhost:8001").rstrip("/")


def _ciudadania_url() -> str:
    return os.environ.get("CIUDADANIA_DIGITAL_URL", "http://localhost:8002").rstrip("/")


def _estado_a_interfaz(estado: str) -> str:
    return {
        "REGISTRADO": "pendiente",
        "APROBADO": "aprobada",
        "RECHAZADO": "rechazada",
    }.get(estado.upper(), estado.lower())
