"""Construye el índice Chroma a partir del corpus normativo en `src/rag/corpus`.

Se ejecuta a mano (`python -m rag.ingest`, con `src` como raíz de import)
cuando el corpus cambia. `main.py` solo abre el índice ya construido, para
que el servicio arranque rápido en lugar de recargar el modelo de embeddings
y reindexar en cada boot.
"""

import datetime
import json
import logging
import re
import shutil
from pathlib import Path

import yaml
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter

from . import configuracion

_logger = logging.getLogger(__name__)

_PATRON_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

# Convención de curación: un prefijo `[TIPO]` al inicio del heading marca qué
# clase de contenido es el chunk, para distinguir un artículo normativo real
# de una sección descriptiva (contexto, definición, procedimiento,
# advertencia) — el splitter de abajo corta por cualquier heading `##` por
# igual, sin esa distinción. Si el heading no trae el prefijo, se asume
# "articulo" (la mayoría de los headings normativos lo son).
_PATRON_TIPO_CHUNK = re.compile(r"^\[(\w+)\]\s*(.*)$")
_TIPOS_CHUNK_VALIDOS = {"articulo", "contexto", "definicion", "procedimiento", "advertencia"}

# Chroma solo acepta valores escalares en la metadata de cada chunk; el
# frontmatter puede traer listas (`normas_relacionadas`) que no aplican aquí.
_TIPOS_METADATA_VALIDOS = (str, int, float, bool)


def _extraer_tipo_chunk(texto_heading: str) -> tuple[str, str]:
    coincidencia = _PATRON_TIPO_CHUNK.match(texto_heading)
    if not coincidencia:
        return "articulo", texto_heading
    tipo = coincidencia.group(1).lower()
    if tipo not in _TIPOS_CHUNK_VALIDOS:
        return "articulo", texto_heading
    return tipo, coincidencia.group(2)


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


def _normalizar_frontmatter(frontmatter: dict) -> dict:
    """YAML parsea fechas (`2025-06-13`) como `datetime.date` y listas
    (`normas_relacionadas`) como `list` — ninguno de los dos es un tipo
    escalar que Chroma acepte en metadata. Se normalizan a string acá, antes
    del filtro de tipos válidos, para que no se pierdan en silencio."""
    normalizado = {}
    for clave, valor in frontmatter.items():
        if isinstance(valor, (datetime.date, datetime.datetime)):
            normalizado[clave] = valor.isoformat()
        elif isinstance(valor, list):
            normalizado[clave] = "; ".join(str(item) for item in valor)
        else:
            normalizado[clave] = valor
    return normalizado


def cargar_chunks(ruta_corpus: Path) -> list[Document]:
    chunks: list[Document] = []
    for ruta in sorted(ruta_corpus.glob("*.md")):
        frontmatter, cuerpo = _leer_documento(ruta)
        frontmatter = _normalizar_frontmatter(frontmatter)

        for fragmento in _dividir_por_articulo(cuerpo):
            metadata = {**frontmatter, **fragmento.metadata}
            if "articulo" in metadata:
                tipo_chunk, texto_limpio = _extraer_tipo_chunk(metadata["articulo"])
                metadata["tipo_chunk"] = tipo_chunk
                metadata["articulo"] = texto_limpio

            descartados = [
                clave for clave, valor in metadata.items() if not isinstance(valor, _TIPOS_METADATA_VALIDOS)
            ]
            if descartados:
                _logger.warning(
                    "%s (%s): se descartan campos de metadata no escalares: %s",
                    ruta.name,
                    metadata.get("articulo", "?"),
                    descartados,
                )

            metadata = {
                clave: valor
                for clave, valor in metadata.items()
                if isinstance(valor, _TIPOS_METADATA_VALIDOS)
            }
            chunks.append(Document(page_content=fragmento.page_content.strip(), metadata=metadata))
    return chunks


def _chunks_actividades() -> list[Document]:
    """Genera los chunks de actividades del formulario en el momento de
    indexar, en vez de copiarlas a mano en un .md: `catalogos/actividades.json`
    es la fuente de verdad que también usa el desplegable del Paso 2
    (`rama-solicitud.js`), así que leerlo acá evita que el corpus quede
    desactualizado si alguien edita el catálogo más adelante. Sin archivo no
    hay chunk: no se contempla su ausencia porque el propio formulario
    depende de que exista.

    Dos chunks separados, no uno solo: la lista literal y la aclaración de
    alcance responden preguntas distintas ("¿qué actividades hay?" vs. "¿mi
    actividad de X cuenta?"), y juntarlas en un párrafo largo diluye la
    señal específica de cada una para el buscador de similitud (mismo
    problema ya visto con el glosario de siglas agrupado)."""
    ruta = configuracion.RAIZ_PROYECTO / "catalogos" / "actividades.json"
    actividades = json.loads(ruta.read_text(encoding="utf-8"))
    lista = ", ".join(actividades[:-1]) + f" y {actividades[-1]}"

    norma = "Catálogo de actividades del formulario (elaboración propia)"
    return [
        Document(
            page_content=(
                f"Las actividades que puedes seleccionar en el Formulario Electrónico, "
                f"al declarar el uso del combustible, son: {lista}."
            ),
            metadata={
                "norma": norma,
                "articulo": "Actividades declarables en el formulario",
                "tipo_chunk": "contexto",
                "es_normativo": False,
            },
        ),
        Document(
            page_content=(
                "El trámite de registro de consumo de combustibles en bidones no está "
                "restringido a ninguna actividad económica en particular: según el "
                "Artículo 2 del Reglamento RAN-ANH-DJ-UGJN N° 0008/2025, aplica a "
                "cualquier persona natural que adquiera combustibles líquidos en "
                "bidones, tambores u otros envases aptos, sin importar su actividad. "
                "Si tu actividad no aparece en la lista del formulario, podés "
                "declararla igual eligiendo la opción \"Otros\"."
            ),
            metadata={
                "norma": norma,
                "articulo": "Alcance del trámite sin importar la actividad",
                "tipo_chunk": "articulo",
                "es_normativo": False,
            },
        ),
    ]


def construir_indice() -> int:
    ruta_corpus = configuracion.ruta_corpus()
    chunks = cargar_chunks(ruta_corpus)
    if not chunks:
        raise RuntimeError(f"No se encontraron documentos .md en {ruta_corpus}.")
    chunks.extend(_chunks_actividades())

    ruta_indice = configuracion.ruta_indice()
    if ruta_indice.exists():
        # `Chroma.from_documents` no reemplaza una colección existente en el
        # mismo `persist_directory`: le agrega los documentos nuevos a los
        # que ya había. Sin este borrado, cada corrida de `ingest.py` sobre
        # un índice ya construido duplica todos los chunks (bug real,
        # encontrado en esta sesión tras varias reconstrucciones: la
        # colección tenía 155 documentos en vez de 31, cinco copias exactas
        # de cada chunk, lo que desplazaba del top-k a chunks distintos que
        # sí correspondía recuperar).
        shutil.rmtree(ruta_indice)

    embeddings = HuggingFaceEmbeddings(
        model_name=configuracion.modelo_embeddings(),
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=configuracion.coleccion(),
        persist_directory=str(ruta_indice),
        # Los embeddings se normalizan (encode_kwargs), así que la colección
        # debe comparar por coseno: si no, Chroma usa L2 por defecto y
        # `similarity_search_with_relevance_scores` devuelve valores fuera de
        # [0, 1] (incluso negativos), rompiendo el umbral de similitud.
        collection_metadata={"hnsw:space": "cosine"},
    )
    return len(chunks)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    total = construir_indice()
    print(f"Índice construido: {total} chunks en {configuracion.ruta_indice()}")
