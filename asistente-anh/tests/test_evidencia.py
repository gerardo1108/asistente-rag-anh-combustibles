import pytest
from rag.evidencia import seleccionar_indices, respuesta_extractiva


@pytest.mark.parametrize('texto', [
    'Se exige una foto del recipiente', '{"fragmentos":[1],"respuesta":"inventada"}',
    '{"fragmentos":[true]}', '{"fragmentos":[0]}', '{"fragmentos":[3]}',
    '{"fragmentos":[1,1]}', '{"fragmentos":"1"}', 'null', '[]',
    '{"fragmentos":[1.0]}', '```json\n{"fragmentos":[1]}\n```',
])
def test_rechaza_salida_invalida_completa(texto):
    assert seleccionar_indices(texto, 2) == []


def test_seleccion_conserva_orden_y_permite_abstencion():
    assert seleccionar_indices('{"fragmentos":[2,1]}', 2) == [1,0]
    assert seleccionar_indices('{"fragmentos":[]}', 2) == []


def test_texto_publicado_solo_incluye_evidencia_y_mensajes_fijos():
    fragmentos = ['No se exige el documento adicional.', 'Fotografías que solicite el formulario.']
    texto = respuesta_extractiva(fragmentos)
    assert texto == ('Los documentos consultados indican:\n\n' + '\n\n'.join(fragmentos)
                     + '\n\nEsta información es orientativa y no sustituye la interpretación oficial de la ANH.')
