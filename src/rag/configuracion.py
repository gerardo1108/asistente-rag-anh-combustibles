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
    valor = os.environ.get("LLM_PROVEEDORES", "groq,gemini")
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
    # Subido de 3 a 5 con datos del golden set (src/rag/evaluacion): al sumar
    # el glosario de siglas, dos preguntas legítimas sobre Ciudadanía Digital
    # empezaron a perder su chunk correcto del top-3 porque entradas del
    # glosario (temáticamente relacionadas, pero no la respuesta) ocupaban
    # esos lugares. Con k=5 vuelven a entrar, sin generar regresiones en el
    # resto del golden set.
    return int(os.environ.get("RAG_K_RESULTADOS", "5"))


def umbral_similitud() -> float:
    return float(os.environ.get("RAG_UMBRAL_SIMILITUD", "0.45"))


def umbral_fuentes() -> float:
    # Más alto que `umbral_similitud()` a propósito: ese umbral decide qué
    # chunks se le pasan como contexto al LLM (conviene generoso, para no
    # perder recall); este decide qué se *muestra* como "Fuentes" al
    # usuario, donde conviene más estricto — un chunk apenas por encima del
    # umbral de retrieval suele ser temáticamente cercano pero no la
    # respuesta real (ver `_construir_fuentes` en rag_core.py). No afecta
    # qué usa el LLM para generar, solo qué se lista.
    return float(os.environ.get("RAG_UMBRAL_FUENTES", "0.50"))
