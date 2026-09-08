import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# Raiz del repositorio: permite ejecutar este script desde cualquier ubicacion.
ROOT = Path(__file__).resolve().parents[1]

# Agrega `src` al path de Python para importar el motor RAG sin empaquetar el proyecto.
sys.path.insert(0, str(ROOT / "src"))

from rag_engine import HybridRAG, LexicalRAG


ENGINES = {
    "lexical": LexicalRAG,
    "hybrid": HybridRAG,
}


def evaluate(mode: str) -> dict:
    """Ejecuta una evaluacion trazable del recuperador RAG.

    La prueba verifica si el fragmento esperado aparece en el primer resultado
    y entre los tres primeros fragmentos recuperados. Tambien calcula MRR
    (Mean Reciprocal Rank), una metrica util para explicar que tan arriba queda
    la evidencia correcta dentro del ranking.
    """

    # Instancia el recuperador con el corpus curado.
    rag = ENGINES[mode](ROOT / "data" / "corpus_normativo.json")

    # Carga las consultas de prueba y su fuente esperada.
    tests = json.loads((ROOT / "eval" / "test_queries.json").read_text(encoding="utf-8"))

    # Contadores de metricas agregadas.
    top1_hits = 0
    top3_hits = 0
    retrieval_total = 0
    overall_hits = 0
    abstention_hits = 0
    abstention_total = 0
    reciprocal_ranks = []
    category_stats = defaultdict(lambda: {"total": 0, "top3_hits": 0})
    cases = []

    print(f"Evaluacion RAG - modo {mode}")
    print("=" * 40)

    # Evalua cada consulta de forma independiente.
    for test in tests:
        # Recupera hasta tres fragmentos candidatos.
        results = rag.retrieve(test["query"], top_k=3)

        # Extrae ids y fuentes para compararlos con la evidencia esperada.
        chunk_ids = [result.chunk.id for result in results]
        sources = [result.chunk.source for result in results]
        expected_no_results = test.get("expected_no_results", False)
        expected_chunk_id = test.get("expected_chunk_id", "")

        # Calcula ranking de la evidencia esperada. Si no aparece, rank queda en None.
        if expected_no_results:
            rank = None
            top1_ok = False
            top3_ok = False
            overall_ok = not results
            abstention_total += 1
            abstention_hits += int(not results)
        else:
            rank = chunk_ids.index(expected_chunk_id) + 1 if expected_chunk_id in chunk_ids else None
            top1_ok = rank == 1
            top3_ok = rank is not None and rank <= 3
            overall_ok = top3_ok
            retrieval_total += 1
            reciprocal_ranks.append(1 / rank if rank else 0.0)
        top1_hits += int(top1_ok)
        top3_hits += int(top3_ok)
        overall_hits += int(overall_ok)

        category = test.get("category", "sin_categoria")
        category_stats[category]["total"] += 1
        category_stats[category]["top3_hits"] += int(top3_ok)

        cases.append(
            {
                "id": test["id"],
                "category": category,
                "query": test["query"],
                "expected_chunk_id": expected_chunk_id,
                "expected_source": test.get("expected_source", ""),
                "expected_no_results": expected_no_results,
                "retrieved_chunk_ids": chunk_ids,
                "retrieved_sources": sources,
                "rank": rank,
                "top1_ok": top1_ok,
                "top3_ok": top3_ok,
                "overall_ok": overall_ok,
            }
        )

        # Imprime evidencia legible para anexar o mostrar en la demo.
        print(f"Caso: {test['id']} [{category}]")
        print(f"Consulta: {test['query']}")
        if expected_no_results:
            print("Esperado: abstencion sin resultados")
        else:
            print(f"Fragmento esperado: {expected_chunk_id}")
            print(f"Fuente esperada: {test['expected_source']}")
        print(f"Fragmentos recuperados: {chunk_ids}")
        print(f"Recuperado: {sources}")
        print(f"Rank esperado: {rank if rank else 'no recuperado'}")
        print(f"Resultado: {'OK' if overall_ok else 'FALLO'}")
        print("-" * 40)

    # Calcula metricas agregadas del set de prueba.
    total = len(tests)
    metrics = {
        "mode": mode,
        "total_cases": total,
        "retrieval_cases": retrieval_total,
        "overall_accuracy": overall_hits / total if total else 0.0,
        "top1_accuracy": top1_hits / retrieval_total if retrieval_total else 0.0,
        "top3_accuracy": top3_hits / retrieval_total if retrieval_total else 0.0,
        "abstention_accuracy": abstention_hits / abstention_total if abstention_total else None,
        "abstention_cases": abstention_total,
        "mean_reciprocal_rank": sum(reciprocal_ranks) / retrieval_total if retrieval_total else 0.0,
        "category_top3_accuracy": {
            category: values["top3_hits"] / values["total"]
            for category, values in sorted(category_stats.items())
        },
        "cases": cases,
    }

    print(f"Precision general: {metrics['overall_accuracy']:.0%} ({overall_hits}/{total})")
    print(f"Precision top-1: {metrics['top1_accuracy']:.0%} ({top1_hits}/{retrieval_total})")
    print(f"Precision top-3: {metrics['top3_accuracy']:.0%} ({top3_hits}/{retrieval_total})")
    if abstention_total:
        print(f"Precision abstencion: {metrics['abstention_accuracy']:.0%} ({abstention_hits}/{abstention_total})")
    print(f"MRR: {metrics['mean_reciprocal_rank']:.2f}")
    return metrics


def main() -> None:
    """Ejecuta la evaluacion para uno o ambos motores disponibles."""

    parser = argparse.ArgumentParser(description="Evalua la recuperacion top-3 del prototipo RAG.")
    parser.add_argument(
        "--mode",
        choices=["lexical", "hybrid", "both"],
        default="hybrid",
        help="Motor a evaluar. Usa 'both' para comparar lexico e hibrido.",
    )
    parser.add_argument(
        "--report",
        default="",
        help="Ruta opcional para guardar un reporte JSON con resultados detallados.",
    )
    args = parser.parse_args()

    modes = ["lexical", "hybrid"] if args.mode == "both" else [args.mode]
    reports = [evaluate(mode) for mode in modes]

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Reporte guardado en: {report_path}")

    # Falla el script si no se cumple el umbral academico definido en el proyecto.
    if any(report["top3_accuracy"] < 0.8 for report in reports):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
