"""Generación del código de trámite."""

import uuid
from datetime import datetime, timezone
from typing import Callable


def generar_codigo_tramite(existe: Callable[[str], bool]) -> str:
    """Genera `ANH-AAAA-XXXXXX`, corto para poder dictarlo por teléfono.

    XXXXXX son 6 caracteres alfanuméricos en mayúsculas tomados de un UUID.
    Se regenera si choca con un código ya existente.
    """
    anio = datetime.now(timezone.utc).year
    while True:
        sufijo = uuid.uuid4().hex[:6].upper()
        codigo = f"ANH-{anio}-{sufijo}"
        if not existe(codigo):
            return codigo


def ahora_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
