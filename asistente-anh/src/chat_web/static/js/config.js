import { PUERTO_BACKEND, PUERTO_CIUDADANIA, PUERTO_RAG } from "/configuracion-servicios.js";

// Mismo host con el que se accedió a esta página (localhost en desktop,
// la IP de LAN si se abre desde otro dispositivo en la red).
const HOST = window.location.hostname;

export const URL_BACKEND_ANH = `http://${HOST}:${PUERTO_BACKEND}`;
export const URL_CIUDADANIA_DIGITAL = `http://${HOST}:${PUERTO_CIUDADANIA}`;
export const URL_RAG = `http://${HOST}:${PUERTO_RAG}`;

// El mock acepta cualquier valor no vacío; se manda igual para que el
// código sea correcto respecto al contrato.
export const API_KEY_ASISTENTE = "asistente-conversacional-demo";

export const TIMEOUT_MS = 30000;
