"""Persistencia de Ciudadanía Digital, detrás de una abstracción (`Almacen`).

SQLite: un archivo, sin servidor, sin dependencias nuevas (el módulo
`sqlite3` es parte de la biblioteca estándar).
"""

import json
import sqlite3
import threading
from pathlib import Path

_CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS titulares (
    numero_documento TEXT PRIMARY KEY,
    tipo_documento TEXT NOT NULL,
    nombres TEXT NOT NULL,
    primer_apellido TEXT NOT NULL,
    segundo_apellido TEXT,
    fecha_nacimiento TEXT NOT NULL,
    genero TEXT,
    correo TEXT,
    celular TEXT,
    estado_cuenta TEXT NOT NULL
)
"""


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
        cur = self._conexion.execute("SELECT COUNT(*) FROM titulares")
        return cur.fetchone()[0]

    def inicializar_si_vacio(self, ruta_semillas: Path) -> int:
        if self.contar() == 0:
            return self.cargar_semillas(ruta_semillas)
        return 0

    def cargar_semillas(self, ruta_semillas: Path) -> int:
        contenido = json.loads(ruta_semillas.read_text(encoding="utf-8"))
        titulares = contenido.get("titulares", [])
        filas = [
            (
                t["numero_documento"],
                t["tipo_documento"],
                t["nombres"],
                t["primer_apellido"],
                t.get("segundo_apellido"),
                t["fecha_nacimiento"],
                t.get("genero"),
                t.get("correo"),
                t.get("celular"),
                t["estado_cuenta"],
            )
            for t in titulares
        ]
        with self._lock, self._conexion:
            self._conexion.executemany(
                """
                INSERT INTO titulares (
                    numero_documento, tipo_documento, nombres, primer_apellido,
                    segundo_apellido, fecha_nacimiento, genero, correo, celular,
                    estado_cuenta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                filas,
            )
        return len(filas)

    def vaciar(self) -> int:
        with self._lock, self._conexion:
            total = self.contar()
            self._conexion.execute("DELETE FROM titulares")
        return total

    def buscar(self, numero_documento: str) -> sqlite3.Row | None:
        cur = self._conexion.execute(
            "SELECT * FROM titulares WHERE numero_documento = ?", (numero_documento,)
        )
        return cur.fetchone()
