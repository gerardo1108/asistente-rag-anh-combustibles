const USA_PROXY = window.location.port === "" || window.location.port === "80" || window.location.port === "443";
export const URL_BACKEND_ANH = USA_PROXY
  ? `${window.location.origin}/api/backend-anh`
  : `http://${window.location.hostname}:8001`;

// El mock acepta cualquier valor no vacío; se manda igual para satisfacer
// el header que exige verificar_clave_supervision.
export const API_KEY_SUPERVISION = "supervisor-panel-demo";

export const TIMEOUT_MS = 30000;

export const POR_PAGINA = 20;
