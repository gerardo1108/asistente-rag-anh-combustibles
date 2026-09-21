/** Carga los catálogos de referencia servidos por server.py en /catalogos. Espejo de src/chat/catalogos.py. */

let cacheUbicaciones = null;
let cacheActividades = null;

export async function cargarUbicaciones() {
  if (!cacheUbicaciones) {
    const respuesta = await fetch("/catalogos/ubicaciones.json");
    cacheUbicaciones = await respuesta.json();
  }
  return cacheUbicaciones;
}

export async function cargarActividades() {
  if (!cacheActividades) {
    const respuesta = await fetch("/catalogos/actividades.json");
    cacheActividades = await respuesta.json();
  }
  return cacheActividades;
}
