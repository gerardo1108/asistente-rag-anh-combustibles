from dataclasses import dataclass, field

from backend_simulado import crear_solicitud, validar_volumen, verificar_ciudadania_digital
from rag_engine import LexicalRAG


REGISTRATION_STEPS = {
    "ask_ci": "Ingresa tu Carnet de Identidad. Para la demo puedes usar 1234567, 7654321 o 4567890.",
    "ask_activity": "Indica la actividad para la que usaras el combustible.",
    "ask_zone": "Indica la zona del tramite: nacional o fronteriza.",
    "ask_fuel": "Indica el tipo de combustible: gasolina o diesel.",
    "ask_volume": "Indica el volumen solicitado en litros.",
    "ask_destino": "Explica brevemente el destino de uso del combustible.",
    "ask_photo": "Para esta demo escribe 'foto ok' para simular que adjuntaste rostro y Carnet de Identidad.",
}


@dataclass
class ConversationSession:
    """Orquestador conversacional del MVP.

    Esta clase concentra la maquina de estados del tramite. La interfaz web le
    entrega mensajes de usuario y recibe mensajes del asistente. Separar esta
    logica facilita explicar el flujo durante la revision y luego reemplazar la
    interfaz sin reescribir el proceso.
    """

    rag: LexicalRAG
    step: str = "idle"
    data: dict = field(default_factory=dict)
    messages: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Mensaje inicial visible cuando se abre el prototipo por primera vez.
        if not self.messages:
            self.messages.append(
                {
                    "role": "assistant",
                    "text": (
                        "Hola. Soy el asistente RAG ANH en modo prototipo. "
                        "Puedes preguntarme por requisitos o escribir 'iniciar registro' "
                        "para completar una solicitud simulada."
                    ),
                }
            )

    def reset(self) -> None:
        """Reinicia la conversacion y descarta datos capturados."""

        self.step = "idle"
        self.data = {}
        self.messages = []
        self.__post_init__()

    def handle(self, user_text: str) -> dict:
        """Procesa un mensaje del usuario y devuelve el estado actualizado."""

        # Normaliza espacios para evitar entradas vacias accidentales.
        user_text = user_text.strip()

        # Si el usuario no escribe nada, se pide repetir sin avanzar de estado.
        if not user_text:
            self._assistant("Escribe una consulta o una respuesta para continuar.")
            return self.snapshot()

        # Registra el mensaje del usuario en el historial.
        self.messages.append({"role": "user", "text": user_text})

        # Comando global para reiniciar la conversacion desde cualquier punto.
        if user_text.lower() in {"reiniciar", "reset", "cancelar"}:
            self.reset()
            self._assistant("Conversacion reiniciada. Puedes hacer una consulta o iniciar un registro.")
            return self.snapshot()

        # Si la conversacion esta en reposo, se interpreta la intencion inicial.
        if self.step == "idle":
            self._handle_idle(user_text)
            return self.snapshot()

        # Si ya inicio el registro, se procesa el dato esperado por la maquina
        # de estados. Cada metodo valida y decide si avanzar o pedir correccion.
        handlers = {
            "ask_ci": self._handle_ci,
            "ask_activity": self._handle_activity,
            "ask_zone": self._handle_zone,
            "ask_fuel": self._handle_fuel,
            "ask_volume": self._handle_volume,
            "ask_destino": self._handle_destino,
            "ask_photo": self._handle_photo,
            "confirm": self._handle_confirmation,
        }
        handlers[self.step](user_text)
        return self.snapshot()

    def snapshot(self) -> dict:
        """Devuelve una copia simple del estado para que la interfaz lo muestre."""

        return {
            "step": self.step,
            "data": dict(self.data),
            "messages": list(self.messages),
            "next_prompt": REGISTRATION_STEPS.get(self.step, ""),
        }

    def _handle_idle(self, user_text: str) -> None:
        """Decide si el mensaje inicia registro, seguimiento o consulta RAG."""

        text = user_text.lower()
        start_registration = (
            "iniciar registro" in text
            or "empezar registro" in text
            or "comenzar registro" in text
            or "registrar solicitud" in text
            or "crear solicitud" in text
        )
        if start_registration:
            self.step = "ask_ci"
            self._assistant(REGISTRATION_STEPS[self.step])
            return

        # Cualquier otra pregunta en reposo se atiende como consulta normativa.
        result = self.rag.answer(user_text)
        sources = "\n".join(
            f"- {source['source']} / {source['section']}"
            for source in result["sources"]
        )
        self._assistant(f"{result['answer']}\n\nFuentes recuperadas:\n{sources or 'Sin fuentes'}")

    def _handle_ci(self, user_text: str) -> None:
        """Valida el CI contra la base simulada de Ciudadania Digital."""

        result = verificar_ciudadania_digital(user_text)
        if not result["registrado"]:
            self._assistant(result["mensaje"] + " Intenta con otro CI simulado.")
            return
        self.data["ci"] = result["ci"]
        self.data["nombre"] = result["nombre"]
        self.step = "ask_activity"
        self._assistant(f"Identidad simulada verificada para {result['nombre']}. {REGISTRATION_STEPS[self.step]}")

    def _handle_activity(self, user_text: str) -> None:
        """Captura la actividad declarada por el interesado."""

        self.data["actividad"] = user_text
        self.step = "ask_zone"
        self._assistant(REGISTRATION_STEPS[self.step])

    def _handle_zone(self, user_text: str) -> None:
        """Valida que la zona sea una de las opciones aceptadas."""

        zone = user_text.lower().strip()
        if zone not in {"nacional", "fronteriza"}:
            self._assistant("La zona debe ser 'nacional' o 'fronteriza'.")
            return
        self.data["zona"] = zone
        self.step = "ask_fuel"
        self._assistant(REGISTRATION_STEPS[self.step])

    def _handle_fuel(self, user_text: str) -> None:
        """Valida el tipo de combustible."""

        fuel = user_text.lower().strip()
        if fuel not in {"gasolina", "diesel"}:
            self._assistant("El combustible debe ser 'gasolina' o 'diesel'.")
            return
        self.data["combustible"] = fuel
        self.step = "ask_volume"
        self._assistant(REGISTRATION_STEPS[self.step])

    def _handle_volume(self, user_text: str) -> None:
        """Convierte y valida el volumen solicitado."""

        try:
            volume = int(user_text)
        except ValueError:
            self._assistant("El volumen debe ser un numero entero de litros.")
            return

        ok, message = validar_volumen(self.data["zona"], volume)
        if not ok:
            self._assistant(message + " Ingresa un volumen permitido.")
            return
        self.data["volumen_litros"] = volume
        self.step = "ask_destino"
        self._assistant(message + " " + REGISTRATION_STEPS[self.step])

    def _handle_destino(self, user_text: str) -> None:
        """Captura el destino de uso declarado."""

        self.data["destino"] = user_text
        self.step = "ask_photo"
        self._assistant(REGISTRATION_STEPS[self.step])

    def _handle_photo(self, user_text: str) -> None:
        """Simula la validacion de fotografia del interesado."""

        if user_text.lower().strip() not in {"foto ok", "ok", "si", "sí"}:
            self._assistant("No se detecto foto valida en la demo. Escribe 'foto ok' para continuar.")
            return
        self.data["foto_validada"] = True
        self.step = "confirm"
        self._assistant(self._summary())

    def _handle_confirmation(self, user_text: str) -> None:
        """Confirma o cancela el registro de la solicitud."""

        text = user_text.lower().strip()
        if text not in {"si", "sí", "confirmar", "confirmo"}:
            self.step = "idle"
            self._assistant("Registro cancelado. Puedes iniciar uno nuevo cuando quieras.")
            return

        solicitud = crear_solicitud(self.data)
        self.step = "idle"
        self.data = {}
        self._assistant(
            f"Solicitud registrada correctamente. Codigo de tramite: {solicitud.codigo}. "
            "Puedes consultar el estado en el bloque de seguimiento o desde el panel evaluador simulado."
        )

    def _summary(self) -> str:
        """Construye el resumen previo a confirmar la solicitud."""

        return (
            "Revisa el resumen antes de enviar:\n"
            f"- CI: {self.data['ci']}\n"
            f"- Nombre: {self.data['nombre']}\n"
            f"- Actividad: {self.data['actividad']}\n"
            f"- Zona: {self.data['zona']}\n"
            f"- Combustible: {self.data['combustible']}\n"
            f"- Volumen: {self.data['volumen_litros']} litros\n"
            f"- Destino: {self.data['destino']}\n\n"
            "Escribe 'si' para registrar la solicitud o 'no' para cancelar."
        )

    def _assistant(self, text: str) -> None:
        """Agrega un mensaje del asistente al historial."""

        self.messages.append({"role": "assistant", "text": text})
