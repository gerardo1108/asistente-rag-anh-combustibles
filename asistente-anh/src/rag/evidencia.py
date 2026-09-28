"""Valida selección de evidencia. Nunca publica redacción libre del LLM."""
import json


def seleccionar_indices(texto: str, cantidad: int) -> list[int]:
    """IDs 1-based únicos; ante cualquier formato ambiguo se rechaza todo."""
    try:
        valor = json.loads(texto)
    except (ValueError, TypeError):
        return []
    if not isinstance(valor, dict) or set(valor) != {'fragmentos'}:
        return []
    indices = valor['fragmentos']
    if not isinstance(indices, list) or len(indices) > cantidad:
        return []
    if any(type(i) is not int or not 1 <= i <= cantidad for i in indices):
        return []
    if len(set(indices)) != len(indices):
        return []
    return [i - 1 for i in indices]


def seleccionar_indices_y_respuesta(texto: str, cantidad: int) -> tuple[list[int], str | None]:
    """Lee la respuesta combinada del RAG sin relajar el validador histórico."""
    try:
        valor = json.loads(texto)
    except (ValueError, TypeError):
        return [], None
    if not isinstance(valor, dict) or set(valor) != {"fragmentos", "respuesta"}:
        return [], None
    indices = valor["fragmentos"]
    respuesta = valor["respuesta"]
    if not isinstance(respuesta, str) or not respuesta.strip():
        return [], None
    if not isinstance(indices, list) or len(indices) > cantidad:
        return [], None
    if any(type(i) is not int or not 1 <= i <= cantidad for i in indices):
        return [], None
    if len(set(indices)) != len(indices):
        return [], None
    return [i - 1 for i in indices], respuesta.strip()


def respuesta_extractiva(fragmentos: list[str]) -> str:
    return ('Los documentos consultados indican:\n\n' + '\n\n'.join(fragmentos)
            + '\n\nEsta información es orientativa y no sustituye la interpretación oficial de la ANH.')
