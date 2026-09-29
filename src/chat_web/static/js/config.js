// Mismo host con el que se accedió a esta página (localhost en desktop,
// la IP de LAN si se abre desde otro dispositivo en la red).
const HOST = window.location.hostname;
// En el despliegue cloud el navegador entra por un único proxy HTTPS. En
// local se conservan los puertos separados de Docker Compose.
const USA_PROXY = window.location.port === "" || window.location.port === "80" || window.location.port === "443";
const BASE_PROXY = `${window.location.origin}/api`;

export const URL_BACKEND_ANH = USA_PROXY ? `${BASE_PROXY}/backend-anh` : `http://${HOST}:8001`;
export const URL_CIUDADANIA_DIGITAL = USA_PROXY ? `${BASE_PROXY}/ciudadania-digital` : `http://${HOST}:8002`;
export const URL_RAG = USA_PROXY ? `${BASE_PROXY}/rag` : `http://${HOST}:8003`;
export const URL_VALIDACION_IMAGENES = USA_PROXY ? `${BASE_PROXY}/validacion-imagenes` : `http://${HOST}:8004`;

// El mock acepta cualquier valor no vacío; se manda igual para que el
// código sea correcto respecto al contrato.
export const API_KEY_ASISTENTE = "asistente-conversacional-demo";

export const TIMEOUT_MS = 30000;

// Cupos de venta según zona (Decreto Supremo N° 5400, Art. 16 Parágrafo III).
// `es_frontera` en catalogos/ubicaciones.json es un proxy geográfico del
// prototipo, no la zonificación oficial — ver catalogos/README.md.
export const LITROS_MAXIMO_FRONTERA = 50;
export const LITROS_MAXIMO_NO_FRONTERA = 120;
