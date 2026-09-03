import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


# Carpeta donde se guardan los datos de prueba del prototipo.
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Archivo local que actua como base de datos simple para la demo.
# Esta ruta esta ignorada por Git para no versionar datos generados durante pruebas.
STORE_PATH = DATA_DIR / "solicitudes_demo.json"


@dataclass
class Solicitud:
    """Modelo de datos de una solicitud registrada en el entorno simulado.

    En una version productiva, estos campos probablemente vivirian en una tabla
    SQL. Para el MVP se mantienen como dataclass para convertirlos facilmente a
    diccionario y JSON.
    """

    codigo: str
    ci: str
    nombre: str
    actividad: str
    zona: str
    combustible: str
    volumen_litros: int
    destino: str
    estado: str
    observacion: str
    creada_en: str


# Base simulada de Ciudadania Digital.
# Permite probar el flujo sin conectarse a la API oficial de AGETIC.
CIUDADANIA_DIGITAL = {
    "1234567": {"nombre": "Ana Choque Mamani", "domicilio": "La Paz"},
    "7654321": {"nombre": "Victor Hugo Flores", "domicilio": "Caranavi"},
    "4567890": {"nombre": "Rafael Quispe Condori", "domicilio": "El Alto"},
}


def verificar_ciudadania_digital(ci: str) -> dict:
    """Simula la verificacion de un Carnet de Identidad.

    Retorna `registrado=True` cuando el CI existe en la base simulada y
    `registrado=False` cuando no existe. Esto cubre el alcance academico sin
    afirmar integracion real con Ciudadania Digital.
    """

    # Limpia espacios accidentales y busca el CI en la base simulada.
    persona = CIUDADANIA_DIGITAL.get(ci.strip())

    # Si no existe, responde con un mensaje entendible para la interfaz.
    if not persona:
        return {
            "registrado": False,
            "mensaje": "No se encontro un registro simulado para ese Carnet de Identidad.",
        }

    # Si existe, combina el CI con los datos personales encontrados.
    return {"registrado": True, "ci": ci.strip(), **persona}


def validar_volumen(zona: str, volumen_litros: int) -> tuple[bool, str]:
    """Aplica la regla de negocio de volumen maximo por zona."""

    # En el prototipo se usa un limite menor para zona fronteriza.
    limite = 50 if zona.lower().strip() == "fronteriza" else 120

    # Si el volumen excede el limite, la solicitud se detiene antes del registro.
    if volumen_litros > limite:
        return False, f"El volumen declarado supera el limite simulado de {limite} litros para zona {zona}."

    # Si cumple la regla, el flujo puede continuar.
    return True, f"El volumen esta dentro del limite simulado de {limite} litros."


def crear_solicitud(datos: dict) -> Solicitud:
    """Crea y persiste una solicitud en el archivo JSON local."""

    # Carga solicitudes existentes para no sobrescribir registros previos.
    solicitudes = listar_solicitudes()

    # Genera un codigo corto, unico para fines de demostracion.
    codigo = f"ANH-{uuid.uuid4().hex[:8].upper()}"

    # Construye el objeto Solicitud con estado inicial pendiente.
    solicitud = Solicitud(
        codigo=codigo,
        ci=datos["ci"],
        nombre=datos["nombre"],
        actividad=datos["actividad"],
        zona=datos["zona"],
        combustible=datos["combustible"],
        volumen_litros=int(datos["volumen_litros"]),
        destino=datos["destino"],
        estado="pendiente",
        observacion="Solicitud registrada en entorno simulado.",
        creada_en=datetime.now().isoformat(timespec="seconds"),
    )

    # Agrega la nueva solicitud al listado en memoria.
    solicitudes.append(asdict(solicitud))

    # Guarda el listado completo en disco.
    _save(solicitudes)
    return solicitud


def consultar_solicitud(codigo: str, ci: str | None = None) -> dict | None:
    """Busca una solicitud por codigo y, opcionalmente, por CI."""

    # Normaliza el codigo para aceptar minusculas o espacios del usuario.
    codigo = codigo.strip().upper()

    # Recorre la base local hasta encontrar una coincidencia.
    for solicitud in listar_solicitudes():
        if solicitud["codigo"].upper() == codigo and (ci is None or solicitud["ci"] == ci.strip()):
            return solicitud

    # Si no aparece coincidencia, la interfaz mostrara un error controlado.
    return None


def listar_solicitudes() -> list[dict]:
    """Devuelve todas las solicitudes registradas en el entorno simulado."""

    # Si aun no existe archivo, no hay solicitudes creadas.
    if not STORE_PATH.exists():
        return []

    # Carga el JSON como lista de diccionarios.
    return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def actualizar_estado(codigo: str, estado: str, observacion: str = "") -> dict | None:
    """Actualiza el estado de una solicitud desde el panel evaluador simulado."""

    # Normaliza el estado para validar contra el conjunto permitido.
    estado = estado.lower().strip()

    # Limita los estados posibles a los definidos en el prototipo.
    if estado not in {"pendiente", "aprobada", "rechazada"}:
        raise ValueError("El estado debe ser pendiente, aprobada o rechazada.")

    # Carga solicitudes existentes.
    solicitudes = listar_solicitudes()

    # Busca por codigo y actualiza la primera coincidencia.
    for solicitud in solicitudes:
        if solicitud["codigo"].upper() == codigo.strip().upper():
            solicitud["estado"] = estado
            solicitud["observacion"] = observacion or f"Solicitud {estado} en entorno simulado."
            _save(solicitudes)
            return solicitud

    # Retorna None si no se encuentra el codigo.
    return None


def _save(solicitudes: list[dict]) -> None:
    """Guarda solicitudes en disco como JSON legible."""

    # Crea la carpeta data si no existe.
    DATA_DIR.mkdir(exist_ok=True)

    # `ensure_ascii=False` mantiene tildes y ñ legibles en el archivo.
    STORE_PATH.write_text(json.dumps(solicitudes, indent=2, ensure_ascii=False), encoding="utf-8")
