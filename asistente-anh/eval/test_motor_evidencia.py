"""Regresión del orquestador; ejecutar en el entorno con requirements-rag."""
import unittest
from unittest.mock import patch, Mock
from langchain_core.documents import Document
from rag import rag_core as r


class EvidenciaMotorTest(unittest.TestCase):
    def setUp(self):
        self.doc = Document(page_content='Fotografías que solicite el formulario.', metadata={'articulo':'Artículo 4'})

    def test_texto_inventado_no_se_publica(self):
        for salida in ['Es obligatoria una foto del recipiente.', '{"fragmentos":[99]}']:
            with self.subTest(salida=salida), patch.object(r, '_recuperar', return_value=[(self.doc, .9)]), patch.object(r, '_generar', return_value=r.ResultadoGeneracion(salida, 'groq', 1)):
                respuesta = r.responder(None, '¿Qué fotos?', None)
                self.assertFalse(respuesta.encontrado)
                self.assertEqual(respuesta.fuentes, [])
                self.assertEqual(respuesta.respuesta, r.MENSAJE_ABSTENCION)

    def test_fuentes_solo_seleccionadas(self):
        otro = Document(page_content='Texto no seleccionado.')
        with patch.object(r, '_recuperar', return_value=[(otro,.8),(self.doc,.9)]), patch.object(r, '_generar', return_value=r.ResultadoGeneracion('{"fragmentos":[2]}','groq',1)):
            salida=r.responder(None,'¿Qué fotos?',None)
            self.assertTrue(salida.encontrado)
            self.assertEqual(len(salida.fuentes),1)
            self.assertIn(self.doc.page_content,salida.respuesta)
            self.assertNotIn(otro.page_content,salida.respuesta)

    def test_reformulacion_no_sustituye_pregunta_original(self):
        with patch.object(r,'_recuperar',side_effect=[[],[(self.doc,.9)]]), patch.object(r,'_reformular_pregunta',return_value='Pregunta reformulada'), patch.object(r,'_generar',return_value=r.ResultadoGeneracion('{"fragmentos":[]}','groq',1)) as generar:
            r.responder(None,'Pregunta original','Historial')
            self.assertEqual(generar.call_args.args[1:3],('Pregunta original','Historial'))

    def test_recuperacion_conserva_evidencia_cercana_sin_incluir_ruido(self):
        motor=Mock()
        motor.vectorstore.similarity_search_with_relevance_scores.return_value=[
            (self.doc,.4267),(Document(page_content='Ruido'),.0296)]
        with patch.dict('os.environ',{},clear=True):
            self.assertEqual(r._recuperar(motor,'¿Fotografías?'),[(self.doc,.4267)])

    def test_sin_evidencia_no_genera(self):
        with patch.object(r,'_recuperar',return_value=[]), patch.object(r,'_reformular_pregunta',return_value=None), patch.object(r,'_generar') as generar:
            self.assertFalse(r.responder(None,'Sin evidencia',None).encontrado)
            generar.assert_not_called()


if __name__ == '__main__':
    unittest.main()
