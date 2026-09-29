"""Servidor estático de la interfaz vanilla del chat (HTML/CSS/JS, sin build step).

Monta tres directorios: los archivos propios de esta interfaz (`static/`) y,
directamente desde la raíz del repo, `catalogos/` y `recursos/` — la misma
fuente de datos que ya usa `src/chat` (Streamlit), sin duplicarla.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# server.py -> chat_web/ -> src/ -> raíz del repo
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_SUPERVISOR = Path(__file__).resolve().parent / "supervisor"

app = FastAPI(title="Chat ANH (vanilla)")


@app.middleware("http")
async def sin_cache(request: Request, call_next):
    """Evita que el navegador cachee JS/CSS mientras se itera en desarrollo."""
    respuesta = await call_next(request)
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


# Los mounts específicos van antes que el catch-all "/": Starlette resuelve
# los Mount en el orden en que se registran.
app.mount("/catalogos", StaticFiles(directory=RAIZ_PROYECTO / "catalogos"), name="catalogos")
app.mount("/recursos", StaticFiles(directory=RAIZ_PROYECTO / "recursos"), name="recursos")
app.mount("/supervisor/css", StaticFiles(directory=RUTA_SUPERVISOR / "css"), name="supervisor-css")
app.mount("/supervisor/js", StaticFiles(directory=RUTA_SUPERVISOR / "js"), name="supervisor-js")


@app.get("/supervisor")
def pagina_supervisor_lista():
    return FileResponse(RUTA_SUPERVISOR / "index.html")


@app.get("/supervisor/solicitud/{codigo}")
def pagina_supervisor_detalle(codigo: str):
    # El servidor ignora `codigo`: siempre sirve el mismo archivo. El
    # detalle.js del panel lee el código real desde `location.pathname`.
    return FileResponse(RUTA_SUPERVISOR / "detalle.html")


app.mount(
    "/",
    StaticFiles(directory=Path(__file__).resolve().parent / "static", html=True),
    name="static",
)
