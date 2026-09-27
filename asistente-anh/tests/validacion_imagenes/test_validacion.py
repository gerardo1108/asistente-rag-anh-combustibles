import base64
from pathlib import Path

from fastapi.testclient import TestClient

from validacion_imagenes import validador_core
from validacion_imagenes.main import crear_app


IMAGEN_LOGO = Path("asistente-anh/recursos/logo-anh.webp").read_bytes()
IMAGEN_BASE64 = base64.b64encode(IMAGEN_LOGO).decode()


def test_servicio_desactivado_no_llama_al_proveedor(monkeypatch):
    monkeypatch.delenv("VALIDACION_IMAGENES_ACTIVA", raising=False)
    with TestClient(crear_app()) as cliente:
        respuesta = cliente.post(
            "/v1/validaciones-imagen",
            json={"contenido_base64": IMAGEN_BASE64, "mime": "image/png"},
        )

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "VALIDACION_IMAGENES_DESACTIVADA"


def test_imagen_valida_con_motor_simulado(monkeypatch):
    monkeypatch.setenv("VALIDACION_IMAGENES_ACTIVA", "true")
    motor = validador_core.MotorValidacion(
        clientes={"gemini": object()}, modelos={"gemini": "test"}, proveedores=["gemini"]
    )

    def generar(_motor, _imagen):
        return validador_core.VeredictoLLM(
            rostro_visible=True,
            documento_visible=True,
            hay_superposicion=False,
            motivo="Imagen de prueba válida.",
        )

    monkeypatch.setitem(validador_core._GENERADORES, "gemini", generar)
    with TestClient(crear_app(motor)) as cliente:
        respuesta = cliente.post(
            "/v1/validaciones-imagen",
            json={"contenido_base64": IMAGEN_BASE64, "mime": "image/png"},
        )

    assert respuesta.status_code == 200
    assert respuesta.json()["veredicto"] == "VALIDA"


def test_base64_invalido_se_rechaza(monkeypatch):
    monkeypatch.setenv("VALIDACION_IMAGENES_ACTIVA", "true")
    motor = validador_core.MotorValidacion(clientes={}, modelos={}, proveedores=[])
    with TestClient(crear_app(motor)) as cliente:
        respuesta = cliente.post(
            "/v1/validaciones-imagen",
            json={"contenido_base64": "no-es-base64", "mime": "image/png"},
        )

    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "IMAGEN_INVALIDA"


def test_mime_no_soportado_se_rechaza(monkeypatch):
    monkeypatch.setenv("VALIDACION_IMAGENES_ACTIVA", "true")
    motor = validador_core.MotorValidacion(clientes={}, modelos={}, proveedores=[])
    with TestClient(crear_app(motor)) as cliente:
        respuesta = cliente.post(
            "/v1/validaciones-imagen",
            json={"contenido_base64": IMAGEN_BASE64, "mime": "application/pdf"},
        )

    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "MIME_NO_SOPORTADO"
