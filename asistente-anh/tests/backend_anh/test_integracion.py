HEADERS = {"X-API-Key": "cualquier-valor"}


def _solicitud_valida(**overrides):
    base = {
        "tramite": "ANH-REGISTRO-CONSUMO-FUERA-TANQUE",
        "version_formulario": "1.0",
        "canal_origen": "ASISTENTE_CONVERSACIONAL",
        "solicitante": {
            "tipo_documento": "CI",
            "numero_documento": "1112223",
            "nombres": "Ana",
            "primer_apellido": "Perez",
            "segundo_apellido": "Lima",
        },
        "datos": [
            {"campo": "departamento", "valor": "La Paz"},
            {"campo": "volumen_litros", "valor": 80},
        ],
        "adjuntos": [
            {
                "tipo": "FOTO_TITULAR_CON_CI",
                "nombre_archivo": "titular.jpg",
                "mime": "image/jpeg",
                "contenido_base64": "ZmFsc28=",
            }
        ],
        "declaracion_jurada": True,
    }
    base.update(overrides)
    return base


def test_registrar_solicitud_devuelve_codigo_y_estado(cliente):
    respuesta = cliente.post("/v1/solicitudes", json=_solicitud_valida(), headers=HEADERS)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "REGISTRADO"
    assert cuerpo["codigo_tramite"].startswith("ANH-")


def test_registrar_sin_api_key_es_401(cliente):
    respuesta = cliente.post("/v1/solicitudes", json=_solicitud_valida())
    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "NO_AUTORIZADO"


def test_registrar_sin_declaracion_jurada_es_422(cliente):
    payload = _solicitud_valida(declaracion_jurada=False)
    respuesta = cliente.post("/v1/solicitudes", json=payload, headers=HEADERS)
    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "DECLARACION_JURADA_REQUERIDA"


def test_registrar_sin_adjuntos_es_422_generico(cliente):
    payload = _solicitud_valida(adjuntos=[])
    respuesta = cliente.post("/v1/solicitudes", json=payload, headers=HEADERS)
    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "SOLICITUD_INVALIDA"


def test_json_malformado_es_400(cliente):
    respuesta = cliente.post(
        "/v1/solicitudes",
        content=b"{no es json",
        headers={**HEADERS, "Content-Type": "application/json"},
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "SOLICITUD_MALFORMADA"


def test_idempotency_key_repetida_devuelve_409_con_mismo_codigo(cliente):
    clave = "9f1c2b74-4d3a-4a51-9f2e-0c7f1d6b8a20"
    payload = _solicitud_valida()
    primera = cliente.post(
        "/v1/solicitudes", json=payload, headers={**HEADERS, "Idempotency-Key": clave}
    )
    assert primera.status_code == 201
    codigo = primera.json()["codigo_tramite"]

    segunda = cliente.post(
        "/v1/solicitudes", json=payload, headers={**HEADERS, "Idempotency-Key": clave}
    )
    assert segunda.status_code == 409
    assert segunda.json()["codigo_tramite"] == codigo


def test_consultar_estado_de_semilla(cliente):
    respuesta = cliente.get("/v1/solicitudes/ANH-2026-000002/estado", headers=HEADERS)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "APROBADO"
    assert "datos" not in cuerpo


def test_consultar_estado_inexistente_es_404(cliente):
    respuesta = cliente.get("/v1/solicitudes/ANH-2026-NOEXISTE/estado", headers=HEADERS)
    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "TRAMITE_NO_ENCONTRADO"
