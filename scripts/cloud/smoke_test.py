"""Prueba por túnel SSH del flujo ANH, usando únicamente datos sintéticos."""
import base64
import json
from urllib.request import Request, urlopen
from pathlib import Path

HEADERS = {'Content-Type': 'application/json', 'X-API-Key': 'prueba-cloud'}

def call(port, path, data=None, method=None):
    req = Request(f'http://127.0.0.1:{port}{path}',
                  data=json.dumps(data).encode() if data is not None else None,
                  headers=HEADERS, method=method)
    with urlopen(req, timeout=90) as r:
        return r.status, json.load(r)

def main():
    results = {}
    for port in (18001, 18002):
        status, body = call(port, '/health')
        assert status == 200
        results[str(port)] = body
    _, identity = call(18002, '/v1/verificacion-ciudadania',
                       {'tipo_documento': 'CI', 'numero_documento': '6789012'})
    photo = base64.b64encode(b'adjunto sintetico prueba Google Cloud').decode()
    status, created = call(18001, '/v1/solicitudes', {
        'tramite': 'ANH-REGISTRO-CONSUMO-FUERA-TANQUE', 'version_formulario': '1.0',
        'solicitante': identity, 'datos': [{'campo': 'volumen_litros', 'valor': 20}],
        'adjuntos': [{'tipo': 'FOTO_TITULAR_CON_CI', 'nombre_archivo': 'prueba.jpg',
                      'mime': 'image/jpeg', 'contenido_base64': photo}],
        'declaracion_jurada': True})
    assert status == 201
    code = created['codigo_tramite']
    path = '/v1/solicitudes/' + code
    assert call(18001, path + '/estado')[1]['estado'] == 'REGISTRADO'
    assert call(18001, path)[1]['adjuntos'][0]['contenido_base64'] == photo
    assert call(18001, path + '/estado', {'estado': 'APROBADO'}, 'PATCH')[0] == 200
    assert call(18001, path + '/estado')[1]['estado'] == 'APROBADO'
    results['flujo'] = {'codigo': code, 'estado': 'APROBADO', 'adjunto_recuperado': True}
    for path in ('/', '/supervisor', '/configuracion-servicios.js'):
        with urlopen('http://127.0.0.1:18080' + path, timeout=30) as r:
            assert r.status == 200
    results['interfaz_http'] = True
    target = Path('docs/evidencias/prueba_cloud_20260924.json')
    target.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
