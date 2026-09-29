def test_health_reporta_registros_de_semilla(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["servicio"] == "backend-anh"
    assert cuerpo["persistencia"] == "sqlite"
    assert cuerpo["registros"] == 3


def test_reiniciar_sin_habilitar_es_403(cliente):
    respuesta = cliente.post("/reiniciar")
    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "REINICIO_NO_HABILITADO"


def test_reiniciar_habilitado_restaura_semillas(cliente_con_reinicio):
    cliente_con_reinicio.patch(
        "/v1/solicitudes/ANH-2026-000001/estado",
        json={"estado": "APROBADO"},
        headers={"X-API-Key": "x"},
    )

    respuesta = cliente_con_reinicio.post("/reiniciar")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "reiniciado"
    assert cuerpo["registros_cargados"] == 3

    estado = cliente_con_reinicio.get(
        "/v1/solicitudes/ANH-2026-000001/estado", headers={"X-API-Key": "x"}
    )
    assert estado.json()["estado"] == "REGISTRADO"
