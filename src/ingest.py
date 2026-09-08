from pathlib import Path

from rag_engine import HybridRAG, LexicalRAG


def main() -> None:
    corpus_path = Path(__file__).resolve().parents[1] / "data" / "corpus_normativo.json"
    lexical = LexicalRAG(corpus_path)
    hybrid = HybridRAG(corpus_path)
    print("Corpus cargado correctamente.")
    print(f"Fragmentos disponibles: {len(lexical.chunks)}")
    print(f"Motor lexico: {lexical.__class__.__name__}")
    print(f"Motor hibrido/vectorial local: {hybrid.__class__.__name__}")
    print(f"Dimensiones vectoriales: {len(hybrid._vocabulary)}")
    by_source = {}
    for chunk in lexical.chunks:
        by_source[chunk.source] = by_source.get(chunk.source, 0) + 1
    for source, count in sorted(by_source.items()):
        print(f"- {source}: {count} fragmento(s)")


if __name__ == "__main__":
    main()
