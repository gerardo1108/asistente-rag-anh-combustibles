import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import backend_simulado
from conversation import ConversationSession
from rag_engine import HybridRAG


class ConversationFlowTest(unittest.TestCase):
    """Pruebas funcionales del registro conversacional.

    Estas pruebas simulan mensajes de usuario sin abrir el navegador. Cubren los
    casos principales que el prototipo debe controlar para reducir errores de
    llenado antes de registrar una solicitud.
    """

    def setUp(self):
        """Crea una sesion limpia y una base temporal para cada prueba."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_store_path = backend_simulado.STORE_PATH
        backend_simulado.STORE_PATH = Path(self.temp_dir.name) / "solicitudes_demo.json"
        self.session = ConversationSession(HybridRAG(ROOT / "data" / "corpus_normativo.json"))

    def tearDown(self):
        """Restaura la ruta original de datos locales al terminar la prueba."""

        backend_simulado.STORE_PATH = self.original_store_path
        self.temp_dir.cleanup()

    def send_many(self, messages):
        """Envia varios mensajes al flujo y devuelve el ultimo estado."""

        snapshot = None
        for message in messages:
            snapshot = self.session.handle(message)
        return snapshot

    def last_assistant_message(self):
        """Obtiene el ultimo mensaje emitido por el asistente."""

        assistant_messages = [
            message["text"]
            for message in self.session.messages
            if message["role"] == "assistant"
        ]
        return assistant_messages[-1]

    def test_successful_registration_creates_pending_request(self):
        snapshot = self.send_many(
            [
                "iniciar registro",
                "1234567",
                "Agricultura",
                "nacional",
                "gasolina",
                "20",
                "Bomba de agua",
                "foto ok",
                "si",
            ]
        )

        solicitudes = backend_simulado.listar_solicitudes()
        self.assertEqual(snapshot["step"], "idle")
        self.assertEqual(len(solicitudes), 1)
        self.assertEqual(solicitudes[0]["ci"], "1234567")
        self.assertEqual(solicitudes[0]["estado"], "pendiente")
        self.assertIn("Solicitud registrada correctamente", self.last_assistant_message())

    def test_unknown_ci_does_not_advance_registration(self):
        snapshot = self.send_many(["iniciar registro", "0000000"])

        self.assertEqual(snapshot["step"], "ask_ci")
        self.assertEqual(backend_simulado.listar_solicitudes(), [])
        self.assertIn("No se encontro", self.last_assistant_message())

    def test_invalid_zone_keeps_user_in_zone_step(self):
        snapshot = self.send_many(["iniciar registro", "1234567", "Agricultura", "urbana"])

        self.assertEqual(snapshot["step"], "ask_zone")
        self.assertIn("nacional", self.last_assistant_message())
        self.assertIn("fronteriza", self.last_assistant_message())

    def test_invalid_fuel_keeps_user_in_fuel_step(self):
        snapshot = self.send_many(
            ["iniciar registro", "1234567", "Agricultura", "nacional", "kerosene"]
        )

        self.assertEqual(snapshot["step"], "ask_fuel")
        self.assertIn("gasolina' o 'diesel", self.last_assistant_message())

    def test_non_numeric_volume_keeps_user_in_volume_step(self):
        snapshot = self.send_many(
            ["iniciar registro", "1234567", "Agricultura", "nacional", "diesel", "veinte"]
        )

        self.assertEqual(snapshot["step"], "ask_volume")
        self.assertIn("numero entero", self.last_assistant_message())

    def test_frontier_volume_above_limit_is_rejected_before_registration(self):
        snapshot = self.send_many(
            ["iniciar registro", "1234567", "Agricultura", "fronteriza", "diesel", "80"]
        )

        self.assertEqual(snapshot["step"], "ask_volume")
        self.assertEqual(backend_simulado.listar_solicitudes(), [])
        self.assertIn("supera el limite simulado de 50 litros", self.last_assistant_message())

    def test_national_volume_above_limit_is_rejected_before_registration(self):
        snapshot = self.send_many(
            ["iniciar registro", "1234567", "Agricultura", "nacional", "diesel", "150"]
        )

        self.assertEqual(snapshot["step"], "ask_volume")
        self.assertEqual(backend_simulado.listar_solicitudes(), [])
        self.assertIn("supera el limite simulado de 120 litros", self.last_assistant_message())

    def test_invalid_photo_keeps_user_in_photo_step(self):
        snapshot = self.send_many(
            [
                "iniciar registro",
                "1234567",
                "Agricultura",
                "nacional",
                "gasolina",
                "20",
                "Bomba de agua",
                "archivo borroso",
            ]
        )

        self.assertEqual(snapshot["step"], "ask_photo")
        self.assertIn("foto valida", self.last_assistant_message())

    def test_cancel_confirmation_does_not_create_request(self):
        snapshot = self.send_many(
            [
                "iniciar registro",
                "1234567",
                "Agricultura",
                "nacional",
                "gasolina",
                "20",
                "Bomba de agua",
                "foto ok",
                "no",
            ]
        )

        self.assertEqual(snapshot["step"], "idle")
        self.assertEqual(backend_simulado.listar_solicitudes(), [])
        self.assertIn("Registro cancelado", self.last_assistant_message())

    def test_normative_question_returns_sources_without_starting_registration(self):
        snapshot = self.session.handle("Que necesito para registrarme?")

        self.assertEqual(snapshot["step"], "idle")
        self.assertIn("Fuentes recuperadas", self.last_assistant_message())
        self.assertEqual(backend_simulado.listar_solicitudes(), [])


if __name__ == "__main__":
    unittest.main()
