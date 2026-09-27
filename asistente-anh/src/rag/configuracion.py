"""Configuración del servicio RAG, leída de variables de entorno."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# rag/ -> src/ -> raíz del proyecto
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]

MENSAJE_API_KEY_FALTANTE = (
    "Falta la variable de entorno GOOGLE_API_KEY. Conseguí una clave gratuita "
    "en https://aistudio.google.com/apikey."
)

PROVEEDORES_LLM_VALIDOS = {"gemini", "groq"}


def google_api_key() -> str:
    clave = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not clave:
        raise RuntimeError(MENSAJE_API_KEY_FALTANTE)
    return clave


def modelo_gemini() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")


def groq_api_key() -> str:
    clave = os.environ.get("GROQ_API_KEY", "").strip()
    if not clave:
        raise RuntimeError(
            "Falta la variable de entorno GROQ_API_KEY (requerida porque 'groq' "
            "está en LLM_PROVEEDORES). Conseguí una clave en "
            "https://console.groq.com/keys."
        )
    return clave


def modelo_groq() -> str:
    return os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")


def proveedores_llm() -> list[str]:
    # El piloto usa un único proveedor explícito para evitar activar Gemini
    # accidentalmente cuando se despliega sin configurar GOOGLE_API_KEY.
    valor = os.environ.get("LLM_PROVEEDORES", "groq")
    proveedores = [p.strip().lower() for p in valor.split(",") if p.strip()]
    if not proveedores:
        raise RuntimeError("LLM_PROVEEDORES no puede quedar vacío.")
    desconocidos = sorted(set(proveedores) - PROVEEDORES_LLM_VALIDOS)
    if desconocidos:
        raise RuntimeError(
            f"LLM_PROVEEDORES tiene proveedores desconocidos: {desconocidos}. "
            f"Válidos: {sorted(PROVEEDORES_LLM_VALIDOS)}."
        )
    return proveedores


def modelo_embeddings() -> str:
    return os.environ.get(
        "RAG_MODELO_EMBEDDINGS", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )


def ruta_corpus() -> Path:
    return Path(os.environ.get("RAG_RUTA_CORPUS", str(RAIZ_PROYECTO / "src" / "rag" / "corpus")))


def ruta_indice() -> Path:
    return Path(os.environ.get("RAG_RUTA_INDICE", str(RAIZ_PROYECTO / "rag_index")))


def coleccion() -> str:
    return os.environ.get("RAG_COLECCION", "rag_anh")


def k_resultados() -> int:
    return int(os.environ.get("RAG_K_RESULTADOS", "3"))


def umbral_similitud() -> float:
    return float(os.environ.get("RAG_UMBRAL_SIMILITUD", "0.40"))
