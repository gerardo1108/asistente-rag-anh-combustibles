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


def respuesta_extractiva(fragmentos: list[str]) -> str:
    return ('Los documentos consultados indican:\n\n' + '\n\n'.join(fragmentos)
            + '\n\nEsta información es orientativa y no sustituye la interpretación oficial de la ANH.')
