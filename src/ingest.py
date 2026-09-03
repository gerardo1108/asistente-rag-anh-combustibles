from pathlib import Path

from rag_engine import LexicalRAG


def main() -> None:
    corpus_path = Path(__file__).resolve().parents[1] / "data" / "corpus_normativo.json"
    rag = LexicalRAG(corpus_path)
    print("Corpus cargado correctamente.")
    print(f"Fragmentos disponibles: {len(rag.chunks)}")
    by_source = {}
    for chunk in rag.chunks:
        by_source[chunk.source] = by_source.get(chunk.source, 0) + 1
    for source, count in sorted(by_source.items()):
        print(f"- {source}: {count} fragmento(s)")


if __name__ == "__main__":
    main()
