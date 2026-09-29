def test_health_reporta_registros_de_semilla(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["servicio"] == "ciudadania-digital"
    assert cuerpo["persistencia"] == "sqlite"
    assert cuerpo["registros"] == 4


def test_reiniciar_sin_habilitar_es_403(cliente):
    respuesta = cliente.post("/reiniciar")
    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "REINICIO_NO_HABILITADO"


def test_reiniciar_habilitado_recarga_semillas(cliente_con_reinicio):
    respuesta = cliente_con_reinicio.post("/reiniciar")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "reiniciado"
    assert cuerpo["registros_eliminados"] == 4
    assert cuerpo["registros_cargados"] == 4
