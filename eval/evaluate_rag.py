import json
import sys
from pathlib import Path

# Raiz del repositorio: permite ejecutar este script desde cualquier ubicacion.
ROOT = Path(__file__).resolve().parents[1]

# Agrega `src` al path de Python para importar el motor RAG sin empaquetar el proyecto.
sys.path.insert(0, str(ROOT / "src"))

from rag_engine import LexicalRAG


def main() -> None:
    """Ejecuta una evaluacion top-3 del recuperador RAG.

    La prueba verifica si la fuente esperada aparece entre los tres primeros
    fragmentos recuperados. Esta metrica corresponde al criterio de recuperacion
    trazable definido para el MVP.
    """

    # Instancia el recuperador con el corpus curado.
    rag = LexicalRAG(ROOT / "data" / "corpus_normativo.json")

    # Carga las consultas de prueba y su fuente esperada.
    tests = json.loads((ROOT / "eval" / "test_queries.json").read_text(encoding="utf-8"))

    # Contador de casos exitosos.
    hits = 0
    print("Evaluacion RAG - prototipo lexico")
    print("=" * 40)

    # Evalua cada consulta de forma independiente.
    for test in tests:
        # Recupera hasta tres fragmentos candidatos.
        results = rag.retrieve(test["query"], top_k=3)

        # Extrae solo los nombres de fuente para compararlos con el esperado.
        sources = [result.chunk.source for result in results]

        # El caso es correcto si la fuente esperada aparece en el top-3.
        ok = test["expected_source"] in sources
        hits += int(ok)

        # Imprime evidencia legible para anexar o mostrar en la demo.
        print(f"Consulta: {test['query']}")
        print(f"Esperado: {test['expected_source']}")
        print(f"Recuperado: {sources}")
        print(f"Resultado: {'OK' if ok else 'FALLO'}")
        print("-" * 40)

    # Calcula la precision agregada del set de prueba.
    accuracy = hits / len(tests) if tests else 0.0
    print(f"Precision top-3: {accuracy:.0%} ({hits}/{len(tests)})")

    # Falla el script si no se cumple el umbral academico definido en el proyecto.
    if accuracy < 0.8:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
