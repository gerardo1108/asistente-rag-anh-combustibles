import json
import math
import re
from dataclasses import dataclass
from pathlib import Path


# Expresion regular usada para extraer palabras y numeros del texto.
# Incluye vocales acentuadas y la letra ñ para conservar terminos en espanol.
TOKEN_RE = re.compile(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9]+")

# Diccionario minimo de sinonimos del dominio.
# Ayuda a que consultas con palabras equivalentes recuperen el mismo fragmento.
# Ejemplo: si el usuario escribe "foto", tambien se busca "fotografia" e "imagen".
SYNONYMS = {
    "carnet": ["ci", "documento", "identidad"],
    "ci": ["carnet", "documento", "identidad"],
    "foto": ["fotografia", "imagen", "rostro"],
    "fotografia": ["foto", "imagen", "rostro"],
    "bidon": ["envase", "tambor"],
    "bidones": ["envases", "tambores"],
    "rechazada": ["rechazo", "rechazada"],
}


@dataclass
class Chunk:
    """Representa un fragmento recuperable del corpus normativo.

    Cada chunk mantiene texto y metadatos de trazabilidad. En una version con
    ChromaDB o FAISS, estos campos serian los metadatos guardados junto al vector.
    """

    id: str
    source: str
    section: str
    text: str


@dataclass
class RetrievalResult:
    """Resultado de una busqueda sobre el corpus."""

    chunk: Chunk
    score: float


class LexicalRAG:
    """Recuperador RAG lexico para el MVP academico.

    Este motor no usa embeddings todavia. Su objetivo es permitir una demo local,
    reproducible y sin API externa, manteniendo la idea central del RAG:

    1. Cargar fragmentos de una base de conocimiento.
    2. Recuperar los fragmentos mas relevantes ante una consulta.
    3. Generar una respuesta sustentada en el fragmento recuperado.
    4. Exponer las fuentes utilizadas para auditoria academica.

    Cuando se incorpore ChromaDB/FAISS, esta clase puede ser reemplazada sin
    cambiar el contrato usado por `src/app.py`: `retrieve()` y `answer()`.
    """

    def __init__(self, corpus_path: str | Path):
        """Inicializa el motor con el corpus indicado.

        `corpus_path` apunta a `data/corpus_normativo.json`, que contiene una
        lista de fragmentos con `id`, `source`, `section` y `text`.
        """

        # Normaliza la ruta recibida para poder usarla como objeto Path.
        self.corpus_path = Path(corpus_path)

        # Carga el JSON y lo transforma en objetos Chunk.
        self.chunks = self._load_chunks(self.corpus_path)

        # Tokeniza cada fragmento una sola vez para evitar repetir trabajo en
        # cada consulta.
        self._doc_tokens = [self._tokenize(chunk.text) for chunk in self.chunks]

        # Calcula el peso IDF de cada palabra. Palabras muy frecuentes pesan
        # menos; palabras mas especificas del dominio pesan mas.
        self._idf = self._compute_idf(self._doc_tokens)

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievalResult]:
        """Recupera los `top_k` fragmentos mas relacionados con la consulta."""

        # Convierte la pregunta del usuario en tokens comparables con el corpus.
        query_tokens = self._tokenize(query)

        # Aqui se acumulan los fragmentos con puntaje positivo.
        scored = []

        # Se recorre cada fragmento junto con sus tokens precalculados.
        for chunk, doc_tokens in zip(self.chunks, self._doc_tokens):
            # Calcula similitud lexica ponderada entre consulta y fragmento.
            score = self._score(query_tokens, doc_tokens)

            # Solo se conservan fragmentos que comparten algun termino relevante.
            if score > 0:
                scored.append(RetrievalResult(chunk=chunk, score=score))

        # Ordena de mayor a menor relevancia para simular el ranking RAG.
        scored.sort(key=lambda item: item.score, reverse=True)

        # Devuelve como maximo los `top_k` fragmentos solicitados.
        return scored[:top_k]

    def answer(self, query: str) -> dict:
        """Genera una respuesta orientativa y trazable a partir del corpus.

        En esta version, la redaccion es determinista: usa el fragmento mejor
        puntuado. En una version con LLM, el fragmento recuperado se inyectaria
        como contexto para redactar la respuesta final.
        """

        # Recupera los tres fragmentos mas relevantes.
        results = self.retrieve(query, top_k=3)

        # Si no hay evidencia en el corpus, se activa una respuesta de abstencion.
        if not results:
            return {
                "answer": (
                    "No encontre sustento suficiente en el corpus disponible. "
                    "Por seguridad, consulta la fuente oficial de la ANH o AGETIC."
                ),
                "sources": [],
                "confidence": 0.0,
            }

        # El primer resultado es el fragmento con mayor puntaje.
        main = results[0].chunk

        # Respuesta base del MVP: cita la fuente, resume desde el fragmento y
        # agrega el descargo de responsabilidad definido en el proyecto.
        answer = (
            f"Segun {main.source}, {main.text} "
            "Recuerda que esta orientacion es informativa y no reemplaza una decision oficial de la ANH."
        )

        # La respuesta se entrega como diccionario para que la interfaz pueda
        # mostrar texto, fuentes y confianza por separado.
        return {
            "answer": answer,
            "sources": [
                {
                    "id": item.chunk.id,
                    "source": item.chunk.source,
                    "section": item.chunk.section,
                    "score": round(item.score, 4),
                }
                for item in results
            ],
            "confidence": round(results[0].score, 4),
        }

    @staticmethod
    def _load_chunks(path: Path) -> list[Chunk]:
        """Lee el corpus JSON y construye la lista de fragmentos."""

        # Lee el archivo completo usando UTF-8 para aceptar tildes y ñ.
        data = json.loads(path.read_text(encoding="utf-8"))

        # Convierte cada diccionario del JSON en un objeto Chunk tipado.
        return [Chunk(**item) for item in data]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Normaliza un texto a tokens utiles para la busqueda.

        Pasos:
        1. Extrae palabras/numeros con `TOKEN_RE`.
        2. Pasa todo a minusculas.
        3. Elimina palabras vacias muy frecuentes.
        4. Expande sinonimos del dominio.
        """

        # Palabras muy frecuentes que no aportan significado para recuperar.
        stopwords = {
            "a", "al", "ante", "como", "con", "de", "del", "el", "en", "es",
            "la", "las", "lo", "los", "o", "para", "por", "que", "se", "si",
            "su", "un", "una", "y",
        }

        # Extrae tokens, normaliza a minusculas y descarta terminos cortos o vacios.
        tokens = [
            token.lower()
            for token in TOKEN_RE.findall(text)
            if token.lower() not in stopwords and len(token) > 2
        ]

        # Lista final de tokens, incluyendo sinonimos.
        expanded = []

        # Por cada token original, conserva el token y agrega sinonimos si existen.
        for token in tokens:
            expanded.append(token)
            expanded.extend(SYNONYMS.get(token, []))
        return expanded

    @staticmethod
    def _compute_idf(documents: list[list[str]]) -> dict[str, float]:
        """Calcula pesos IDF para destacar terminos especificos del corpus."""

        # Cantidad total de documentos o fragmentos.
        total = len(documents)

        # Vocabulario unico construido a partir de todos los fragmentos.
        vocabulary = set(token for doc in documents for token in set(doc))

        # Diccionario token -> peso IDF.
        idf = {}

        # Calcula cuantas veces aparece cada token en documentos distintos.
        for token in vocabulary:
            document_frequency = sum(1 for doc in documents if token in set(doc))

            # Formula IDF suavizada para evitar divisiones por cero y pesos extremos.
            idf[token] = math.log((1 + total) / (1 + document_frequency)) + 1
        return idf

    def _score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        """Calcula un puntaje simple de similitud consulta-fragmento.

        Se parece a una version minima de TF-IDF:
        - TF: frecuencia del termino dentro del fragmento.
        - IDF: importancia del termino dentro de todo el corpus.
        - Normalizacion: divide por la raiz del largo del fragmento para no
          favorecer textos largos por tener mas palabras.
        """

        # Sin tokens no hay nada que comparar.
        if not query_tokens or not doc_tokens:
            return 0.0

        # Cuenta cuantas veces aparece cada token dentro del fragmento.
        doc_counts = {token: doc_tokens.count(token) for token in set(doc_tokens)}

        # Acumulador del puntaje de similitud.
        score = 0.0

        # Suma puntaje solo para tokens de la consulta presentes en el fragmento.
        for token in query_tokens:
            if token in doc_counts:
                score += (1 + math.log(doc_counts[token])) * self._idf.get(token, 1.0)

        # Normaliza por longitud para que fragmentos largos no dominen el ranking.
        return score / math.sqrt(len(doc_tokens))
