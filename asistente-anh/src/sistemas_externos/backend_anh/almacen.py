"""Persistencia del Backend ANH, detrás de una abstracción (`Almacen`).

SQLite: un archivo, sin servidor, sin dependencias nuevas (el módulo
`sqlite3` es parte de la biblioteca estándar). La persistencia se mantiene
separada de la lógica de las rutas para que el código sea más simple de
probar y de razonar, no porque vaya a cambiar de motor.
"""

import base64
import json
import logging
import sqlite3
import threading
from pathlib import Path

from .codigos import ahora_iso, generar_codigo_tramite
from .errores import ErrorAplicacion
from .modelos import (
    Adjunto,
    CampoFormulario,
    EstadoSolicitud,
    ResumenSolicitud,
    Solicitante,
    SolicitudCreada,
    SolicitudDetalle,
    SolicitudRequest,
)

logger = logging.getLogger(__name__)

_CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS solicitudes (
    codigo_tramite TEXT PRIMARY KEY,
    tramite TEXT NOT NULL,
    version_formulario TEXT NOT NULL,
    canal_origen TEXT NOT NULL,
    solicitante_json TEXT NOT NULL,
    datos_json TEXT NOT NULL,
    adjuntos_json TEXT NOT NULL,
    declaracion_jurada INTEGER NOT NULL,
    estado TEXT NOT NULL,
    fecha_registro TEXT NOT NULL,
    fecha_resolucion TEXT,
    motivo_rechazo TEXT,
    idempotency_key TEXT UNIQUE
)
"""


def _codificar_imagen(ruta_imagenes: Path, nombre_archivo: str) -> str:
    ruta = ruta_imagenes / nombre_archivo
    if not ruta.exists():
        alternativa = ruta_imagenes / f"PENDIENTE_{nombre_archivo}.txt"
        if alternativa.exists():
            logger.warning(
                "Imagen de semilla pendiente, usando placeholder: %s", nombre_archivo
            )
            ruta = alternativa
        else:
            logger.warning("Imagen de semilla no encontrada: %s", nombre_archivo)
            return ""
    return base64.b64encode(ruta.read_bytes()).decode("ascii")


class Almacen:
    def __init__(self, ruta_db: Path | str):
        self._conexion = sqlite3.connect(str(ruta_db), check_same_thread=False)
        self._conexion.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock, self._conexion:
            self._conexion.execute(_CREAR_TABLA)

    def cerrar(self) -> None:
        self._conexion.close()

    def contar(self) -> int:
        cur = self._conexion.execute("SELECT COUNT(*) FROM solicitudes")
        return cur.fetchone()[0]

    def inicializar_si_vacio(self, ruta_semillas: Path, ruta_imagenes: Path) -> int:
        if self.contar() == 0:
            return self.cargar_semillas(ruta_semillas, ruta_imagenes)
        return 0

    def cargar_semillas(self, ruta_semillas: Path, ruta_imagenes: Path) -> int:
        contenido = json.loads(ruta_semillas.read_text(encoding="utf-8"))
        solicitudes = contenido.get("solicitudes", [])
        filas = []
        for s in solicitudes:
            adjuntos = [
                {
                    "tipo": a["tipo"],
                    "nombre_archivo": a["archivo"],
                    "mime": a.get("mime", "image/jpeg"),
                    "contenido_base64": _codificar_imagen(ruta_imagenes, a["archivo"]),
                }
                for a in s["adjuntos"]
            ]
            filas.append(
                (
                    s["codigo_tramite"],
                    s["tramite"],
                    s["version_formulario"],
                    s["canal_origen"],
                    json.dumps(s["solicitante"], ensure_ascii=False),
                    json.dumps(s["datos"], ensure_ascii=False),
                    json.dumps(adjuntos, ensure_ascii=False),
                    1 if s["declaracion_jurada"] else 0,
                    s["estado"],
                    s["fecha_registro"],
                    s.get("fecha_resolucion"),
                    s.get("motivo_rechazo"),
                    None,
                )
            )
        with self._lock, self._conexion:
            self._conexion.executemany(
                """
                INSERT INTO solicitudes (
                    codigo_tramite, tramite, version_formulario, canal_origen,
                    solicitante_json, datos_json, adjuntos_json, declaracion_jurada,
                    estado, fecha_registro, fecha_resolucion, motivo_rechazo,
                    idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                filas,
            )
        return len(filas)

    def vaciar(self) -> int:
        with self._lock, self._conexion:
            total = self.contar()
            self._conexion.execute("DELETE FROM solicitudes")
        return total

    def existe_codigo(self, codigo: str) -> bool:
        cur = self._conexion.execute(
            "SELECT 1 FROM solicitudes WHERE codigo_tramite = ?", (codigo,)
        )
        return cur.fetchone() is not None

    def buscar_por_idempotency_key(self, clave: str) -> SolicitudCreada | None:
        cur = self._conexion.execute(
            "SELECT codigo_tramite, fecha_registro FROM solicitudes WHERE idempotency_key = ?",
            (clave,),
        )
        fila = cur.fetchone()
        if fila is None:
            return None
        return SolicitudCreada(
            codigo_tramite=fila["codigo_tramite"], fecha_registro=fila["fecha_registro"]
        )

    def crear(
        self, payload: SolicitudRequest, idempotency_key: str | None
    ) -> SolicitudCreada:
        codigo = generar_codigo_tramite(self.existe_codigo)
        fecha_registro = ahora_iso()
        with self._lock, self._conexion:
            self._conexion.execute(
                """
                INSERT INTO solicitudes (
                    codigo_tramite, tramite, version_formulario, canal_origen,
                    solicitante_json, datos_json, adjuntos_json, declaracion_jurada,
                    estado, fecha_registro, fecha_resolucion, motivo_rechazo,
                    idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    codigo,
                    payload.tramite,
                    payload.version_formulario,
                    payload.canal_origen,
                    json.dumps(payload.solicitante.model_dump(), ensure_ascii=False),
                    json.dumps(
                        [c.model_dump(exclude_none=True) for c in payload.datos],
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        [a.model_dump() for a in payload.adjuntos], ensure_ascii=False
                    ),
                    1 if payload.declaracion_jurada else 0,
                    "REGISTRADO",
                    fecha_registro,
                    None,
                    None,
                    idempotency_key,
                ),
            )
        return SolicitudCreada(codigo_tramite=codigo, fecha_registro=fecha_registro)

    def _obtener_fila(self, codigo: str) -> sqlite3.Row | None:
        cur = self._conexion.execute(
            "SELECT * FROM solicitudes WHERE codigo_tramite = ?", (codigo,)
        )
        return cur.fetchone()

    def obtener_estado(self, codigo: str) -> EstadoSolicitud | None:
        fila = self._obtener_fila(codigo)
        if fila is None:
            return None
        return EstadoSolicitud(
            codigo_tramite=fila["codigo_tramite"],
            tramite=fila["tramite"],
            estado=fila["estado"],
            fecha_registro=fila["fecha_registro"],
            fecha_resolucion=fila["fecha_resolucion"],
            motivo_rechazo=fila["motivo_rechazo"],
        )

    def listar(
        self, estado: str | None, pagina: int, por_pagina: int, q: str | None = None
    ) -> tuple[int, list[ResumenSolicitud]]:
        condicion = "WHERE estado = ?" if estado else ""
        parametros: list = [estado] if estado else []

        # El nombre del solicitante no es una columna propia: vive adentro
        # de solicitante_json. Para poder buscar por nombre hay que
        # decodificar primero, así que a diferencia del filtro por estado
        # (columna real), la paginación de la búsqueda por `q` se resuelve
        # en Python sobre la lista ya decodificada, no con LIMIT/OFFSET en
        # SQL. Intrascendente en rendimiento para el puñado de registros de
        # un prototipo.
        filas = self._conexion.execute(
            f"""
            SELECT * FROM solicitudes {condicion}
            ORDER BY fecha_registro DESC
            """,
            parametros,
        ).fetchall()

        resumenes = []
        for fila in filas:
            solicitante = Solicitante(**json.loads(fila["solicitante_json"]))
            resumenes.append(
                ResumenSolicitud(
                    codigo_tramite=fila["codigo_tramite"],
                    tramite=fila["tramite"],
                    solicitante=solicitante.nombre_completo(),
                    numero_documento=solicitante.numero_documento,
                    estado=fila["estado"],
                    fecha_registro=fila["fecha_registro"],
                )
            )

        if q:
            q_normalizado = q.strip().lower()
            resumenes = [
                r
                for r in resumenes
                if q_normalizado in r.solicitante.lower()
                or q_normalizado in r.numero_documento.lower()
            ]

        total = len(resumenes)
        inicio = (pagina - 1) * por_pagina
        return total, resumenes[inicio : inicio + por_pagina]

    def obtener_detalle(self, codigo: str) -> SolicitudDetalle | None:
        fila = self._obtener_fila(codigo)
        if fila is None:
            return None
        return SolicitudDetalle(
            codigo_tramite=fila["codigo_tramite"],
            tramite=fila["tramite"],
            version_formulario=fila["version_formulario"],
            canal_origen=fila["canal_origen"],
            solicitante=Solicitante(**json.loads(fila["solicitante_json"])),
            datos=[CampoFormulario(**c) for c in json.loads(fila["datos_json"])],
            adjuntos=[Adjunto(**a) for a in json.loads(fila["adjuntos_json"])],
            declaracion_jurada=bool(fila["declaracion_jurada"]),
            estado=fila["estado"],
            fecha_registro=fila["fecha_registro"],
            fecha_resolucion=fila["fecha_resolucion"],
            motivo_rechazo=fila["motivo_rechazo"],
        )

    def resolver(
        self, codigo: str, estado: str, motivo_rechazo: str | None
    ) -> EstadoSolicitud:
        fila = self._obtener_fila(codigo)
        if fila is None:
            raise ErrorAplicacion(
                404,
                "TRAMITE_NO_ENCONTRADO",
                "No se encontró un trámite con el código indicado.",
            )
        if fila["estado"] != "REGISTRADO" and estado != "REGISTRADO":
            raise ErrorAplicacion(
                409,
                "TRAMITE_YA_RESUELTO",
                "La solicitud ya fue resuelta. Reabrila como REGISTRADO antes de cambiar la decisión.",
            )
        fecha_resolucion = None if estado == "REGISTRADO" else ahora_iso()
        motivo_rechazo = None if estado == "REGISTRADO" else motivo_rechazo
        with self._lock, self._conexion:
            self._conexion.execute(
                """
                UPDATE solicitudes
                SET estado = ?, fecha_resolucion = ?, motivo_rechazo = ?
                WHERE codigo_tramite = ?
                """,
                (estado, fecha_resolucion, motivo_rechazo, codigo),
            )
        return EstadoSolicitud(
            codigo_tramite=fila["codigo_tramite"],
            tramite=fila["tramite"],
            estado=estado,
            fecha_registro=fila["fecha_registro"],
            fecha_resolucion=fecha_resolucion,
            motivo_rechazo=motivo_rechazo,
        )
