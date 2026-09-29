from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sistemas_externos.ciudadania_digital.almacen import Almacen
from sistemas_externos.ciudadania_digital.main import crear_app

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_SEMILLAS = RAIZ_PROYECTO / "semillas" / "titulares.json"


def _app_de_prueba(tmp_path):
    almacen = Almacen(tmp_path / "prueba.db")
    app = crear_app(almacen=almacen, ruta_semillas=RUTA_SEMILLAS)
    return app, almacen


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.delenv("PERMITIR_REINICIO", raising=False)
    app, almacen = _app_de_prueba(tmp_path)
    with TestClient(app) as cliente:
        yield cliente
    almacen.cerrar()


@pytest.fixture
def cliente_con_reinicio(tmp_path, monkeypatch):
    monkeypatch.setenv("PERMITIR_REINICIO", "true")
    app, almacen = _app_de_prueba(tmp_path)
    with TestClient(app) as cliente:
        yield cliente
    almacen.cerrar()
