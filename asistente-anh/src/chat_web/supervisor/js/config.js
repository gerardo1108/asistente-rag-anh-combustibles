import { PUERTO_BACKEND } from "/configuracion-servicios.js";

export const URL_BACKEND_ANH = `http://${window.location.hostname}:${PUERTO_BACKEND}`;

// El mock acepta cualquier valor no vacío; se manda igual para satisfacer
// el header que exige verificar_clave_supervision.
export const API_KEY_SUPERVISION = "supervisor-panel-demo";

export const TIMEOUT_MS = 30000;

export const POR_PAGINA = 20;
