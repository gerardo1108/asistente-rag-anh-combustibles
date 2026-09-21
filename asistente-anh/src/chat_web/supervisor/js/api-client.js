/**
 * Cliente HTTP al Backend ANH, operaciones de supervisión
 * (`contratos/openapi-supervision-anh.yaml`). Variante propia del
 * `api-client.js` del chat ciudadano —no lo importa— para no tocar ese
 * archivo; la duplicación es solo el wrapper genérico de fetch/errores, no
 * lógica de negocio: los datos siguen viniendo del mismo Almacen.
 */

import { API_KEY_SUPERVISION, TIMEOUT_MS, URL_BACKEND_ANH } from "./config.js";

export class ApiError extends Error {
  constructor(statusCode, mensaje, codigo = null) {
    super(mensaje);
    this.statusCode = statusCode;
    this.mensaje = mensaje;
    this.codigo = codigo;
  }
}

async function peticion(metodo, url, { body } = {}) {
  const controlador = new AbortController();
  const idTimeout = setTimeout(() => controlador.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, {
      method: metodo,
      headers: {
        "X-API-Key": API_KEY_SUPERVISION,
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
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

/** {estado?, pagina, porPagina, q?} -> {total, pagina, porPagina, solicitudes} */
export async function listarSolicitudes({ estado, pagina, porPagina, q }) {
  const params = new URLSearchParams({ pagina: String(pagina), por_pagina: String(porPagina) });
  if (estado) params.set("estado", estado);
  if (q) params.set("q", q);

  const respuesta = await peticion("GET", `${URL_BACKEND_ANH}/v1/solicitudes?${params}`);
  if (!respuesta.ok) throw await errorDesdeRespuesta(respuesta);
  return respuesta.json();
}

export async function obtenerSolicitud(codigo) {
  const respuesta = await peticion(
    "GET",
    `${URL_BACKEND_ANH}/v1/solicitudes/${encodeURIComponent(codigo)}`,
  );
  if (!respuesta.ok) throw await errorDesdeRespuesta(respuesta);
  return respuesta.json();
}

/** Aprobar y rechazar son el mismo endpoint: PATCH .../estado con distinto payload. */
export async function resolverSolicitud(codigo, estado, motivoRechazo) {
  const respuesta = await peticion(
    "PATCH",
    `${URL_BACKEND_ANH}/v1/solicitudes/${encodeURIComponent(codigo)}/estado`,
    { body: { estado, motivo_rechazo: motivoRechazo ?? null } },
  );
  if (!respuesta.ok) throw await errorDesdeRespuesta(respuesta);
  return respuesta.json();
}
