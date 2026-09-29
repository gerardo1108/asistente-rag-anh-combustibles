"""Evalúa la calidad del retrieval del RAG contra `golden_set.json`: un set de
preguntas con la norma/artículo que deberían recuperar. No requiere API keys
de LLM — solo prueba la etapa de recuperación (embeddings + Chroma), no la
generación, así que sirve para ajustar `k`/umbral con datos antes de tocar
la generación.

Requiere el índice ya construido (`python -m rag.ingest`).

Uso: `cd src && python -m rag.evaluacion.evaluar_retrieval`
"""

import json
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from .. import configuracion

_RUTA_GOLDEN_SET = Path(__file__).resolve().parent / "golden_set.json"


def _cargar_vectorstore() -> Chroma:
    embeddings = HuggingFaceEmbeddings(
        model_name=configuracion.modelo_embeddings(),
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return Chroma(
        collection_name=configuracion.coleccion(),
        embedding_function=embeddings,
        persist_directory=str(configuracion.ruta_indice()),
        collection_metadata={"hnsw:space": "cosine"},
    )


def evaluar() -> None:
    casos = json.loads(_RUTA_GOLDEN_SET.read_text(encoding="utf-8"))
    vectorstore = _cargar_vectorstore()
    k = configuracion.k_resultados()
    umbral = configuracion.umbral_similitud()

    aciertos = 0
    for caso in casos:
        resultados = vectorstore.similarity_search_with_relevance_scores(caso["pregunta"], k=k)
        relevantes = [(doc, score) for doc, score in resultados if score >= umbral]
        acierto = any(
            doc.metadata.get("norma") == caso["norma_esperada"]
            and doc.metadata.get("articulo") == caso["articulo_esperado"]
            for doc, _ in relevantes
        )
        aciertos += acierto
        mejor = resultados[0] if resultados else None
        supera_umbral = bool(relevantes)
        detalle = (
            f"{mejor[0].metadata.get('norma')} / {mejor[0].metadata.get('articulo')} "
            f"(score={mejor[1]:.3f}{'' if supera_umbral else ', bajo umbral'})"
            if mejor
            else "sin candidatos"
        )
        print(f"[{'OK  ' if acierto else 'FAIL'}] {caso['pregunta']}")
        print(f"       esperado: {caso['norma_esperada']} / {caso['articulo_esperado']}")
        print(f"       obtenido: {detalle}\n")

    print(f"Resultado: {aciertos}/{len(casos)} preguntas recuperaron la fuente esperada "
          f"(k={k}, umbral={umbral}).")


if __name__ == "__main__":
    evaluar()
