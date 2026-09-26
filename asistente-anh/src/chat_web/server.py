"""Servidor estático de la interfaz vanilla del chat (HTML/CSS/JS, sin build step).

Monta tres directorios: los archivos propios de esta interfaz (`static/`) y,
directamente desde la raíz del repo, `catalogos/` y `recursos/` — la misma
fuente de datos que ya usa `src/chat` (Streamlit), sin duplicarla.
"""

import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

# server.py -> chat_web/ -> src/ -> raíz del repo
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_SUPERVISOR = Path(__file__).resolve().parent / "supervisor"

app = FastAPI(title="Chat ANH (vanilla)")

SERVICIOS = {
    "backend": os.getenv("BACKEND_URL", "http://127.0.0.1:8001"),
    "ciudadania": os.getenv("CIUDADANIA_URL", "http://127.0.0.1:8002"),
    "rag": os.getenv("RAG_URL", "http://127.0.0.1:8003"),
}


@app.middleware("http")
async def sin_cache(request: Request, call_next):
    """Evita que el navegador cachee JS/CSS mientras se itera en desarrollo."""
    respuesta = await call_next(request)
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@app.get("/configuracion-servicios.js")
def configuracion_servicios():
    return Response(
        "export const URL_BACKEND_ANH = '/api/backend';\n"
        "export const URL_CIUDADANIA_DIGITAL = '/api/ciudadania';\n"
        "export const URL_RAG = '/api/rag';\n",
        media_type="application/javascript",
    )


@app.api_route("/api/{servicio}/{ruta:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
async def proxy_servicio(servicio: str, ruta: str, request: Request):
    """Mantiene las APIs detrás del mismo origen para acceso remoto temporal."""
    base = SERVICIOS.get(servicio)
    if base is None:
        return Response("Servicio no disponible", status_code=404)
    contenido = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() in {"content-type", "x-api-key", "idempotency-key"}}
    async with httpx.AsyncClient(timeout=30.0) as cliente:
        respuesta = await cliente.request(
            request.method,
            f"{base}/{ruta}",
            params=request.query_params,
            content=contenido,
            headers=headers,
        )
    respuesta_headers = {k: v for k, v in respuesta.headers.items() if k.lower() in {"content-type", "content-length"}}
    return Response(respuesta.content, status_code=respuesta.status_code, headers=respuesta_headers)


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
