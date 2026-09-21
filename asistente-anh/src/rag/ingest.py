"""Construye el índice Chroma a partir del corpus normativo en `src/rag/corpus`.

Se ejecuta a mano (`python -m rag.ingest`, con `src` como raíz de import)
cuando el corpus cambia. `main.py` solo abre el índice ya construido, para
que el servicio arranque rápido en lugar de recargar el modelo de embeddings
y reindexar en cada boot.
"""

import re
from pathlib import Path

import yaml
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter

from . import configuracion

_PATRON_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

# Chroma solo acepta valores escalares en la metadata de cada chunk; el
# frontmatter puede traer listas (`normas_relacionadas`) que no aplican aquí.
_TIPOS_METADATA_VALIDOS = (str, int, float, bool)


def _leer_documento(ruta: Path) -> tuple[dict, str]:
    texto = ruta.read_text(encoding="utf-8")
    coincidencia = _PATRON_FRONTMATTER.match(texto)
    if not coincidencia:
        raise ValueError(f"{ruta} no tiene frontmatter YAML (bloque --- ... ---).")
    frontmatter = yaml.safe_load(coincidencia.group(1)) or {}
    cuerpo = coincidencia.group(2)
    return frontmatter, cuerpo


def _dividir_por_articulo(cuerpo: str) -> list[Document]:
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("##", "articulo")])
    return splitter.split_text(cuerpo)


def cargar_chunks(ruta_corpus: Path) -> list[Document]:
    chunks: list[Document] = []
    for ruta in sorted(ruta_corpus.glob("*.md")):
        frontmatter, cuerpo = _leer_documento(ruta)
        for fragmento in _dividir_por_articulo(cuerpo):
            metadata = {**frontmatter, **fragmento.metadata}
            metadata = {
                clave: valor
                for clave, valor in metadata.items()
                if isinstance(valor, _TIPOS_METADATA_VALIDOS)
            }
            chunks.append(Document(page_content=fragmento.page_content.strip(), metadata=metadata))
    return chunks


def construir_indice() -> int:
    ruta_corpus = configuracion.ruta_corpus()
    chunks = cargar_chunks(ruta_corpus)
    if not chunks:
        raise RuntimeError(f"No se encontraron documentos .md en {ruta_corpus}.")

    embeddings = HuggingFaceEmbeddings(
        model_name=configuracion.modelo_embeddings(),
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=configuracion.coleccion(),
        persist_directory=str(configuracion.ruta_indice()),
        # Los embeddings se normalizan (encode_kwargs), así que la colección
        # debe comparar por coseno: si no, Chroma usa L2 por defecto y
        # `similarity_search_with_relevance_scores` devuelve valores fuera de
        # [0, 1] (incluso negativos), rompiendo el umbral de similitud.
        collection_metadata={"hnsw:space": "cosine"},
    )
    return len(chunks)


if __name__ == "__main__":
    total = construir_indice()
    print(f"Índice construido: {total} chunks en {configuracion.ruta_indice()}")
