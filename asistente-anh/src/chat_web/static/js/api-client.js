/**
 * Clientes HTTP a los tres servicios que consume la interfaz.
 * Espejo de src/chat/cliente_api.py: mismos endpoints, mismos headers,
 * mismo tratamiento de errores (incluida la asimetría entre el esquema de
 * error de RAG, {mensaje}, y el de los otros dos servicios, {codigo,
 * mensaje, detalles?}).
 */

import { API_KEY_ASISTENTE, TIMEOUT_MS, URL_BACKEND_ANH, URL_CIUDADANIA_DIGITAL, URL_RAG } from "./config.js";

export class ApiError extends Error {
  constructor(statusCode, mensaje, codigo = null) {
    super(mensaje);
    this.statusCode = statusCode;
    this.mensaje = mensaje;
    this.codigo = codigo;
  }
}

async function peticion(metodo, url, { headers = {}, body } = {}) {
  const controlador = new AbortController();
  const idTimeout = setTimeout(() => controlador.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, {
      method: metodo,
      headers: body !== undefined ? { "Content-Type": "application/json", ...headers } : headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controlador.signal,
    });
  } catch {
    throw new ApiError(503, "No se pudo conectar con el servicio. ¿Está corriendo?");
  } finally {
    clearTimeout(idTimeout);
  }
}

async function errorDesdeRespuesta(respuesta) {
  let cuerpo = null;
  try {
    cuerpo = await respuesta.json();
  } catch {
    // cuerpo no es JSON válido: se ignora, mensaje cae al genérico de abajo
  }
  const mensaje = cuerpo?.mensaje ?? `Error inesperado del servicio (HTTP ${respuesta.status}).`;
  return new ApiError(respuesta.status, mensaje, cuerpo?.codigo ?? null);
}

export async function consultarRag(pregunta) {
  const respuesta = await peticion("POST", `${URL_RAG}/v1/consultas-rag`, {
    body: { pregunta },
  });
  if (!respuesta.ok) throw await errorDesdeRespuesta(respuesta);
  return respuesta.json();
}

export async function verificarCiudadania(tipoDocumento, numeroDocumento) {
  const respuesta = await peticion("POST", `${URL_CIUDADANIA_DIGITAL}/v1/verificacion-ciudadania`, {
    headers: { "X-API-Key": API_KEY_ASISTENTE },
    body: { tipo_documento: tipoDocumento, numero_documento: numeroDocumento },
  });
  if (!respuesta.ok) throw await errorDesdeRespuesta(respuesta);
  return respuesta.json();
}

/** Devuelve {body, esDuplicado}: un 409 (reintento con la misma Idempotency-Key) es éxito, no error. */
export async function registrarSolicitud(sobre, idempotencyKey) {
  const respuesta = await peticion("POST", `${URL_BACKEND_ANH}/v1/solicitudes`, {
    headers: { "X-API-Key": API_KEY_ASISTENTE, "Idempotency-Key": idempotencyKey },
    body: sobre,
  });
  if (respuesta.status === 201 || respuesta.status === 409) {
    return { body: await respuesta.json(), esDuplicado: respuesta.status === 409 };
  }
  throw await errorDesdeRespuesta(respuesta);
}

export async function consultarEstado(codigoTramite) {
  const respuesta = await peticion(
    "GET",
    `${URL_BACKEND_ANH}/v1/solicitudes/${encodeURIComponent(codigoTramite)}/estado`,
    { headers: { "X-API-Key": API_KEY_ASISTENTE } },
  );
  if (!respuesta.ok) throw await errorDesdeRespuesta(respuesta);
  return respuesta.json();
}

/** Texto de la burbuja de "Ver estado", redactado por LLM (RAG, sin auth). */
export async function generarTextoEstado(datos) {
  const respuesta = await peticion("POST", `${URL_RAG}/v1/generar-texto-estado`, { body: datos });
  if (!respuesta.ok) throw await errorDesdeRespuesta(respuesta);
  return respuesta.json();
}
