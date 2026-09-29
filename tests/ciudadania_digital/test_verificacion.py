HEADERS = {"X-API-Key": "cualquier-valor"}


def test_verificar_titular_habilitado(cliente):
    respuesta = cliente.post(
        "/v1/verificacion-ciudadania",
        json={"tipo_documento": "CI", "numero_documento": "6789012"},
        headers=HEADERS,
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["nombres"] == "Juan Carlos"
    assert cuerpo["primer_apellido"] == "Mamani"
    assert cuerpo["fecha_nacimiento"] == "1985-03-14"


def test_verificar_sin_api_key_es_401(cliente):
    respuesta = cliente.post(
        "/v1/verificacion-ciudadania",
        json={"tipo_documento": "CI", "numero_documento": "6789012"},
    )
    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "NO_AUTORIZADO"


def test_verificar_no_registrado_es_404(cliente):
    respuesta = cliente.post(
        "/v1/verificacion-ciudadania",
        json={"tipo_documento": "CI", "numero_documento": "0000000"},
        headers=HEADERS,
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "NO_REGISTRADO"


def test_verificar_cuenta_bloqueada_es_409(cliente):
    respuesta = cliente.post(
        "/v1/verificacion-ciudadania",
        json={"tipo_documento": "CI", "numero_documento": "5556677"},
        headers=HEADERS,
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "CUENTA_BLOQUEADA"


def test_verificar_requiere_revalidacion_es_409(cliente):
    respuesta = cliente.post(
        "/v1/verificacion-ciudadania",
        json={"tipo_documento": "CI", "numero_documento": "9087654"},
        headers=HEADERS,
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "REQUIERE_REVALIDACION"


def test_documento_con_formato_invalido_es_400(cliente):
    respuesta = cliente.post(
        "/v1/verificacion-ciudadania",
        json={"tipo_documento": "CI", "numero_documento": "abc-123"},
        headers=HEADERS,
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "DOCUMENTO_INVALIDO"


def test_falta_numero_documento_es_400(cliente):
    respuesta = cliente.post(
        "/v1/verificacion-ciudadania", json={"tipo_documento": "CI"}, headers=HEADERS
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "DOCUMENTO_INVALIDO"


def test_json_malformado_es_400(cliente):
    respuesta = cliente.post(
        "/v1/verificacion-ciudadania",
        content=b"{no es json",
        headers={**HEADERS, "Content-Type": "application/json"},
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "DOCUMENTO_INVALIDO"
