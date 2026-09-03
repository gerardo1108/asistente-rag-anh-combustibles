import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from backend_simulado import (
    actualizar_estado,
    consultar_solicitud,
    listar_solicitudes,
)
from conversation import ConversationSession
from rag_engine import LexicalRAG


# Raiz del repositorio. Se usa para construir rutas absolutas independientes
# del directorio desde donde se ejecute el script.
ROOT = Path(__file__).resolve().parents[1]

# Instancia global del recuperador. Se carga una sola vez al iniciar el servidor
# para que cada consulta reutilice el corpus ya procesado.
RAG = LexicalRAG(ROOT / "data" / "corpus_normativo.json")

# Sesion conversacional global del prototipo academico.
# Para una demo local alcanza con una sesion compartida; una version productiva
# deberia crear una sesion por usuario.
SESSION = ConversationSession(RAG)


# Plantilla HTML del prototipo.
# Se mantiene en una cadena para que el MVP funcione solo con librerias estandar.
# Las llaves dobles `{{` y `}}` son necesarias porque luego se usa `.format()`.
HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Asistente RAG ANH - Prototipo</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f6f7f9; color: #17202a; }}
    header {{ background: #075985; color: white; padding: 18px 28px; }}
    main {{ display: grid; grid-template-columns: 1.25fr 0.75fr; gap: 18px; padding: 18px; }}
    section {{ background: white; border: 1px solid #d8dee6; border-radius: 8px; padding: 16px; }}
    h1 {{ margin: 0; font-size: 24px; }}
    h2 {{ margin-top: 0; color: #075985; font-size: 19px; }}
    label {{ display: block; font-weight: bold; margin-top: 10px; }}
    input, select, textarea {{ width: 100%; box-sizing: border-box; padding: 9px; border: 1px solid #b8c2cc; border-radius: 6px; margin-top: 4px; }}
    button {{ margin-top: 12px; padding: 10px 14px; border: 0; border-radius: 6px; background: #0f766e; color: white; font-weight: bold; cursor: pointer; }}
    button.secondary {{ background: #334155; }}
    pre, .answer {{ white-space: pre-wrap; background: #f1f5f9; padding: 12px; border-radius: 6px; border: 1px solid #d8dee6; }}
    .chat {{ display: grid; gap: 10px; max-height: 560px; overflow-y: auto; padding-right: 4px; }}
    .message {{ border-radius: 8px; padding: 10px 12px; line-height: 1.45; white-space: pre-wrap; }}
    .assistant {{ background: #eef6ff; border: 1px solid #bfdbfe; }}
    .user {{ background: #ecfdf5; border: 1px solid #a7f3d0; margin-left: 48px; }}
    .quick {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }}
    .quick button {{ margin-top: 0; background: #075985; }}
    .danger {{ background: #9f1239; }}
    .status {{ background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; padding: 10px; margin-top: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid #d8dee6; text-align: left; padding: 8px; vertical-align: top; }}
    .notice {{ color: #475569; font-size: 14px; }}
    @media (max-width: 900px) {{ main {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<header>
  <h1>Asistente RAG ANH - prototipo academico</h1>
  <p>Orientacion normativa, registro simulado y seguimiento de solicitud.</p>
</header>
<main>
  <section>
    <h2>Asistente conversacional</h2>
    <div class="chat">{chat_history}</div>
    <form method="post" action="/chat">
      <label>Mensaje</label>
      <textarea name="message" rows="3" placeholder="Pregunta algo o escribe: iniciar registro"></textarea>
      <button>Enviar mensaje</button>
    </form>
    <div class="quick">
      <form method="post" action="/chat"><input type="hidden" name="message" value="iniciar registro"><button>Iniciar registro</button></form>
      <form method="post" action="/chat"><input type="hidden" name="message" value="Que necesito para registrarme?"><button>Consultar requisitos</button></form>
      <form method="post" action="/chat"><input type="hidden" name="message" value="Cuantos litros puedo declarar en zona fronteriza?"><button>Limites de litros</button></form>
      <form method="post" action="/reset"><button class="danger">Reiniciar chat</button></form>
    </div>
    <div class="status">
      <strong>Estado del flujo:</strong> {conversation_step}<br>
      <strong>Siguiente dato esperado:</strong> {next_prompt}
    </div>
  </section>
  <section>
    <h2>Seguimiento y panel ANH</h2>
    <form method="post" action="/status">
      <label>Codigo de tramite</label>
      <input name="codigo" placeholder="ANH-XXXXXXXX" value="{codigo}">
      <label>CI</label>
      <input name="ci" value="{status_ci}" placeholder="Ej. 1234567">
      <button>Consultar estado</button>
    </form>
    <pre>{status_result}</pre>
    <h2>Panel evaluador simulado</h2>
    {panel}
    <p class="notice">Este panel solo actualiza datos del entorno de prueba local.</p>
  </section>
</main>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    """Controlador HTTP del prototipo.

    Esta clase recibe las peticiones del navegador y las enruta a las funciones
    del MVP:

    - `/chat`: conversacion guiada para consulta o registro.
    - `/status`: consulta de estado de una solicitud.
    - `/update`: actualizacion desde el panel evaluador simulado.
    """

    # Estado de la interfaz durante la sesion del servidor.
    # No es una sesion por usuario; es suficiente para una demo local controlada.
    state = {
        "status_result": "",
        "codigo": "",
        "status_ci": "",
    }

    def do_GET(self):
        """Renderiza la pagina principal cuando el navegador hace GET /."""

        self._render()

    def do_HEAD(self):
        """Responde comprobaciones de disponibilidad sin enviar el HTML completo."""

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_POST(self):
        """Procesa formularios enviados desde la interfaz web."""

        # Lee la longitud del cuerpo HTTP para saber cuantos bytes consumir.
        length = int(self.headers.get("Content-Length", 0))

        # Lee el cuerpo, lo decodifica como texto y lo interpreta como formulario.
        params = parse_qs(self.rfile.read(length).decode("utf-8"))

        # `parse_qs` devuelve listas; este MVP toma el primer valor de cada campo.
        data = {key: values[0] for key, values in params.items()}

        # Enrutamiento simple segun la URL del formulario.
        if self.path == "/chat":
            self._chat(data)
        elif self.path == "/reset":
            self._reset()
        elif self.path == "/status":
            self._status(data)
        elif self.path == "/update":
            self._update(data)

        # Despues de procesar la accion, vuelve a dibujar la pantalla.
        self._render()

    def _chat(self, data):
        """Envia un mensaje al orquestador conversacional."""

        # La interfaz solo pasa el texto; la logica del flujo vive en ConversationSession.
        snapshot = SESSION.handle(data.get("message", ""))

        # Si el ultimo mensaje del asistente contiene un codigo, se intenta
        # precargar el formulario de seguimiento para acelerar la demostracion.
        latest = snapshot["messages"][-1]["text"] if snapshot["messages"] else ""
        if "Codigo de tramite:" in latest:
            codigo = latest.split("Codigo de tramite:", 1)[1].split(".", 1)[0].strip()
            self.state["codigo"] = codigo
            solicitud = consultar_solicitud(codigo)
            if solicitud:
                self.state["status_ci"] = solicitud["ci"]

    def _reset(self):
        """Reinicia el chat y limpia resultados de seguimiento."""

        SESSION.reset()
        self.state["status_result"] = ""
        self.state["codigo"] = ""
        self.state["status_ci"] = ""

    def _status(self, data):
        """Consulta el estado de una solicitud por codigo y CI."""

        # Busca la solicitud en el almacenamiento local.
        solicitud = consultar_solicitud(data.get("codigo", ""), data.get("ci", ""))

        # Mantiene los datos de busqueda visibles en el formulario.
        self.state["codigo"] = data.get("codigo", "")
        self.state["status_ci"] = data.get("ci", "")

        # Muestra la solicitud encontrada o un error controlado.
        self.state["status_result"] = json.dumps(
            solicitud or {"error": "Solicitud no encontrada en el entorno simulado."},
            indent=2,
            ensure_ascii=False,
        )

    def _update(self, data):
        """Actualiza el estado desde el panel evaluador simulado."""

        actualizar_estado(data["codigo"], data["estado"], data.get("observacion", ""))

    def _render(self):
        """Construye y envia el HTML final al navegador."""

        # Genera la tabla del panel evaluador con las solicitudes actuales.
        panel = render_panel()

        # Escapa los valores visibles para evitar que entradas del usuario rompan
        # el HTML o inserten etiquetas.
        body = HTML.format(
            **{key: html.escape(str(value)) for key, value in self.state.items()},
            chat_history=render_chat_history(),
            conversation_step=html.escape(SESSION.step),
            next_prompt=html.escape(SESSION.snapshot()["next_prompt"] or "Puedes consultar normativa o iniciar registro."),
            panel=panel,
        )

        # Encabezados HTTP minimos para responder HTML en UTF-8.
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        # Envia el cuerpo de la respuesta al navegador.
        self.wfile.write(body.encode("utf-8"))


def render_panel() -> str:
    """Construye la tabla HTML del panel evaluador simulado."""

    # Lista acumuladora de filas HTML.
    rows = []

    # Cada solicitud registrada se muestra como una fila editable.
    for solicitud in listar_solicitudes():
        # Escapa el codigo antes de insertarlo en HTML.
        codigo = html.escape(solicitud["codigo"])

        # Construye una fila con estado actual y formulario para actualizar.
        rows.append(
            f"<tr><td>{codigo}</td><td>{html.escape(solicitud['nombre'])}</td>"
            f"<td>{html.escape(solicitud['estado'])}</td>"
            f"<td><form method='post' action='/update'>"
            f"<input type='hidden' name='codigo' value='{codigo}'>"
            f"<select name='estado'><option>aprobada</option><option>rechazada</option><option>pendiente</option></select>"
            f"<input name='observacion' placeholder='Observacion'>"
            f"<button class='secondary'>Actualizar</button></form></td></tr>"
        )

    # Si no hay registros, se muestra un mensaje simple.
    if not rows:
        return "<p>No hay solicitudes registradas todavia.</p>"

    # Devuelve la tabla completa con encabezados y filas.
    return "<table><tr><th>Codigo</th><th>Interesado</th><th>Estado</th><th>Accion</th></tr>" + "".join(rows) + "</table>"


def render_chat_history() -> str:
    """Convierte el historial conversacional en bloques HTML."""

    # Cada mensaje recibe una clase segun el rol para distinguir usuario/asistente.
    bubbles = []
    for message in SESSION.messages:
        role = html.escape(message["role"])
        text = html.escape(message["text"])
        label = "Usuario" if role == "user" else "Asistente"
        bubbles.append(f"<div class='message {role}'><strong>{label}</strong><br>{text}</div>")
    return "".join(bubbles)


def main():
    """Inicia el servidor local del prototipo."""

    # ThreadingHTTPServer permite atender varias peticiones sencillas durante la demo.
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)

    # Mensaje para que el equipo sepa que URL abrir.
    print("Prototipo disponible en http://127.0.0.1:8000")

    # Mantiene el servidor escuchando hasta que se interrumpa con Ctrl+C.
    server.serve_forever()


if __name__ == "__main__":
    # Punto de entrada cuando se ejecuta: python src/app.py
    main()
