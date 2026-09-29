HEADERS = {"X-API-Key": "clave-supervision"}


def test_listar_solicitudes_incluye_las_de_semilla(cliente):
    respuesta = cliente.get("/v1/solicitudes", headers=HEADERS)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 3
    assert len(cuerpo["solicitudes"]) == 3
    assert "datos" not in cuerpo["solicitudes"][0]


def test_listar_solicitudes_filtra_por_estado(cliente):
    respuesta = cliente.get(
        "/v1/solicitudes", params={"estado": "APROBADO"}, headers=HEADERS
    )
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["solicitudes"][0]["codigo_tramite"] == "ANH-2026-000002"


def test_listar_solicitudes_busca_por_nombre_parcial_sin_distinguir_mayusculas(cliente):
    respuesta = cliente.get("/v1/solicitudes", params={"q": "mamani"}, headers=HEADERS)
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["solicitudes"][0]["codigo_tramite"] == "ANH-2026-000001"


def test_listar_solicitudes_busca_por_numero_documento_parcial(cliente):
    respuesta = cliente.get("/v1/solicitudes", params={"q": "45219"}, headers=HEADERS)
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["solicitudes"][0]["codigo_tramite"] == "ANH-2026-000002"


def test_listar_solicitudes_busqueda_sin_coincidencias(cliente):
    respuesta = cliente.get(
        "/v1/solicitudes", params={"q": "nombre-inexistente"}, headers=HEADERS
    )
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 0
    assert cuerpo["solicitudes"] == []


def test_obtener_detalle_incluye_datos_y_adjuntos(cliente):
    respuesta = cliente.get("/v1/solicitudes/ANH-2026-000001", headers=HEADERS)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["solicitante"]["nombres"] == "Juan Carlos"
    assert len(cuerpo["datos"]) == 8
    assert len(cuerpo["adjuntos"]) == 1


def test_obtener_detalle_inexistente_es_404(cliente):
    respuesta = cliente.get("/v1/solicitudes/ANH-2026-NOEXISTE", headers=HEADERS)
    assert respuesta.status_code == 404


def test_resolver_aprobado(cliente):
    respuesta = cliente.patch(
        "/v1/solicitudes/ANH-2026-000001/estado",
        json={"estado": "APROBADO"},
        headers=HEADERS,
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "APROBADO"
    assert cuerpo["fecha_resolucion"] is not None


def test_resolver_rechazado_sin_motivo_es_422(cliente):
    respuesta = cliente.patch(
        "/v1/solicitudes/ANH-2026-000001/estado",
        json={"estado": "RECHAZADO"},
        headers=HEADERS,
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "MOTIVO_RECHAZO_REQUERIDO"


def test_resolver_ya_resuelto_es_409(cliente):
    respuesta = cliente.patch(
        "/v1/solicitudes/ANH-2026-000002/estado",
        json={"estado": "APROBADO"},
        headers=HEADERS,
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "TRAMITE_YA_RESUELTO"


def test_resolver_inexistente_es_404(cliente):
    respuesta = cliente.patch(
        "/v1/solicitudes/ANH-2026-NOEXISTE/estado",
        json={"estado": "APROBADO"},
        headers=HEADERS,
    )
    assert respuesta.status_code == 404
