"""Recorrido de contratos de la V2 sin llamadas a proveedores LLM."""
import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from chat_web.server import app as chat
from sistemas_externos.backend_anh.almacen import Almacen as AlmacenAnh
from sistemas_externos.backend_anh.main import crear_app as crear_anh
from sistemas_externos.ciudadania_digital.almacen import Almacen as AlmacenCD
from sistemas_externos.ciudadania_digital.main import crear_app as crear_cd

RAIZ = Path(__file__).resolve().parents[1]
HEADERS = {"X-API-Key": "prueba-v2"}


@pytest.mark.parametrize("estado_final", ["APROBADO", "RECHAZADO"])
def test_identidad_registro_supervision_y_persistencia(tmp_path, estado_final):
    db_cd = AlmacenCD(tmp_path / "cd.db")
    db_anh = AlmacenAnh(tmp_path / "anh.db")
    app_cd = crear_cd(db_cd, RAIZ / "semillas/titulares.json")
    app_anh = crear_anh(db_anh, RAIZ / "semillas/solicitudes.json", RAIZ / "semillas/imagenes")
    try:
        with TestClient(app_cd) as cd, TestClient(app_anh) as anh:
            identidad = cd.post("/v1/verificacion-ciudadania", headers=HEADERS,
                                json={"tipo_documento": "CI", "numero_documento": "6789012"})
            assert identidad.status_code == 200
            # Evidencia sintética; los mocks almacenan bytes sin validar la imagen.
            foto = base64.b64encode(b"adjunto sintetico de prueba").decode()
            payload = {
                "tramite": "ANH-REGISTRO-CONSUMO-FUERA-TANQUE",
                "version_formulario": "1.0", "solicitante": identidad.json(),
                "datos": [{"campo": "volumen_litros", "valor": 20}],
                "adjuntos": [{"tipo": "FOTO_TITULAR_CON_CI", "nombre_archivo": "prueba.jpg",
                              "mime": "image/jpeg", "contenido_base64": foto}],
                "declaracion_jurada": True,
            }
            registro = anh.post("/v1/solicitudes", headers=HEADERS, json=payload)
            assert registro.status_code == 201
            codigo = registro.json()["codigo_tramite"]
            ruta = f"/v1/solicitudes/{codigo}"
            assert anh.get(ruta + "/estado", headers=HEADERS).json()["estado"] == "REGISTRADO"
            assert anh.get(ruta, headers=HEADERS).json()["adjuntos"][0]["contenido_base64"] == foto
            resolucion = {"estado": estado_final}
            if estado_final == "RECHAZADO":
                resolucion["motivo_rechazo"] = "Corregir la fotografía de prueba"
            assert anh.patch(ruta + "/estado", headers=HEADERS, json=resolucion).status_code == 200
            seguimiento = anh.get(ruta + "/estado", headers=HEADERS).json()
            assert seguimiento["estado"] == estado_final
            if estado_final == "RECHAZADO":
                assert seguimiento["motivo_rechazo"] == resolucion["motivo_rechazo"]
    finally:
        db_cd.cerrar()
        db_anh.cerrar()
    reabierto = AlmacenAnh(tmp_path / "anh.db")
    try:
        assert reabierto.obtener_estado(codigo).estado == estado_final
    finally:
        reabierto.cerrar()


def test_paginas_y_recursos_de_la_interfaz():
    with TestClient(chat) as cliente:
        for ruta in ("/", "/supervisor", "/supervisor/solicitud/ANH-2026-000001",
                     "/js/main.js", "/catalogos/actividades.json", "/recursos/logo-anh.webp"):
            assert cliente.get(ruta).status_code == 200, ruta


def test_puerto_publico_configurable_sin_exponer_secretos(monkeypatch):
    monkeypatch.setenv("BACKEND_PORT", "18001")
    monkeypatch.setenv("GOOGLE_API_KEY", "secreto-de-prueba")
    with TestClient(chat) as cliente:
        respuesta = cliente.get("/configuracion-servicios.js")
        assert respuesta.status_code == 200
        assert "PUERTO_BACKEND = 18001" in respuesta.text
        assert "secreto-de-prueba" not in respuesta.text
