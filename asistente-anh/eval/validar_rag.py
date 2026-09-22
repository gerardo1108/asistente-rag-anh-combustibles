"""Prueba HTTP de humo del RAG; requiere servicio activo y consume cuota LLM.

No mide precisión general ni valida jurídicamente el corpus. Conserva las
respuestas para revisión humana, además de comprobar fuentes y abstención.
"""
import argparse
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

CASOS = [
    ("requisitos", {"pregunta": "¿Qué información mínima es obligatoria en el Formulario Electrónico?"}, True, "Artículo 4"),
    ("fotografias", {"pregunta": "¿El registro exige fotografías y datos personales?"}, True, "Artículo 4"),
    ("seguimiento_contexto", {"pregunta": "¿Y qué datos debo completar?", "contexto_conversacion": "Estoy consultando el Formulario Electrónico de registro de consumidores de combustibles líquidos en bidones."}, True, "Artículo 4"),
    ("fuera_alcance", {"pregunta": "¿Cómo preparo una tarta de chocolate?"}, False, None),
    ("dato_ausente", {"pregunta": "¿Cuál es el número de teléfono personal del director actual de la ANH?"}, False, None),
    ("volumen_no_documentado", {"pregunta": "¿Cuál es el límite exacto de litros por día en zona fronteriza? Si no figura en los documentos, no inventes una cifra."}, None, None),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8003")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    resultados = []
    for nombre, datos, encontrado, articulo in CASOS:
        inicio = time.monotonic()
        request = Request(args.url.rstrip('/') + '/v1/consultas-rag',
                          data=json.dumps(datos).encode(), headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=90) as response:
            salida = json.load(response)
        correcto = ((encontrado is None or salida["encontrado"] == encontrado)
                    and (not articulo or any(articulo in f["articulo"] for f in salida["fuentes"]))
                    and (encontrado is not False or not salida["fuentes"]))
        resultados.append({"caso": nombre, "entrada": datos, "resultado": salida,
                           "segundos": round(time.monotonic() - inicio, 2),
                           "comprobacion_automatica": correcto,
                           "requiere_revision_humana": True})
        print(nombre, ('REVISIÓN MANUAL' if encontrado is None else 'OK') if correcto else 'REVISAR', flush=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(resultados, ensure_ascii=False, indent=2) + '\n')
    if not all(r['comprobacion_automatica'] for r in resultados):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
