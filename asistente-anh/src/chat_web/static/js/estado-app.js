/**
 * Router de 3 ramas fijas. Espejo de src/chat/app.py, con una diferencia
 * deliberada: las 3 ramas mantienen su DOM y su estado en memoria todo el
 * tiempo (cambiar de pestaña solo oculta/muestra, nunca destruye ni
 * reinicia). El reinicio es una acción explícita por pestaña, no un efecto
 * secundario de navegar entre ellas.
 */

import * as ramaEstado from "./rama-estado.js";
import * as ramaNormativa from "./rama-normativa.js";
import * as ramaSolicitud from "./rama-solicitud.js";

const RAMAS = [
  { id: "normativa", etiqueta: "Consultar", modulo: ramaNormativa },
  { id: "solicitud", etiqueta: "Registrar formulario", modulo: ramaSolicitud },
  { id: "estado", etiqueta: "Ver estado", modulo: ramaEstado },
];

const SVG_REINICIAR =
  '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#3F3F3A" stroke-width="2" ' +
  'stroke-linecap="round" stroke-linejoin="round">' +
  '<path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M21 3v5h-5"></path>' +
  '<path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path><path d="M3 21v-5h5"></path></svg>';

let ramaActualId = RAMAS[0].id;

// contenedores persistentes por rama: id -> { panelContenido, panelRama }
const panelesPorRama = new Map();

export function inicializar() {
  const nav = document.getElementById("nav");
  nav.innerHTML = "";
  // Los 3 botones van agrupados en una píldora blanca centrada en la barra
  // de nav (no sueltos directo sobre el degradado de .zona-superior).
  const grupoNav = document.createElement("div");
  grupoNav.className = "nav-grupo";
  for (const rama of RAMAS) {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "nav-item";
    boton.textContent = rama.etiqueta;
    boton.dataset.rama = rama.id;
    boton.addEventListener("click", () => cambiarRama(rama.id));
    grupoNav.appendChild(boton);
  }
  nav.appendChild(grupoNav);

  const botonReiniciar = document.createElement("button");
  botonReiniciar.type = "button";
  botonReiniciar.className = "boton-reiniciar-nav";
  botonReiniciar.title = "Reiniciar el chat activo";
  botonReiniciar.innerHTML = SVG_REINICIAR;
  // Closure sobre `ramaActualId` (no un valor fijado acá): siempre reinicia
  // la pestaña activa al momento del click, sin importar cuál era al montar
  // este botón único.
  botonReiniciar.addEventListener("click", () => reiniciarRama(ramaActualId));
  nav.appendChild(botonReiniciar);

  const contenido = document.getElementById("contenido");
  contenido.innerHTML = "";
  for (const rama of RAMAS) {
    const panelRama = document.createElement("div");
    panelRama.className = `panel-rama panel-rama-${rama.id} oculto`;

    const panelContenido = document.createElement("div");
    panelContenido.className = "panel-rama-contenido";
    panelRama.appendChild(panelContenido);

    contenido.appendChild(panelRama);
    panelesPorRama.set(rama.id, { panelRama, panelContenido });

    // mostrar() se invoca una única vez por rama, acá: cambiar de pestaña
    // después de esto solo oculta/muestra el panel, nunca lo reconstruye.
    rama.modulo.mostrar(panelContenido);
  }

  render();
}

function cambiarRama(id) {
  if (id === ramaActualId) return;
  ramaActualId = id;
  render();
}

function reiniciarRama(id) {
  const rama = ramaPorId(id);
  const { panelContenido } = panelesPorRama.get(id);
  rama.modulo.reset();
  panelContenido.innerHTML = "";
  rama.modulo.mostrar(panelContenido);
  rama.modulo.alMostrar?.();
}

function ramaPorId(id) {
  return RAMAS.find((rama) => rama.id === id);
}

function render() {
  document.querySelectorAll(".nav-item").forEach((boton) => {
    boton.classList.toggle("activo", boton.dataset.rama === ramaActualId);
  });
  for (const [id, { panelRama }] of panelesPorRama) {
    panelRama.classList.toggle("oculto", id !== ramaActualId);
  }
  ramaPorId(ramaActualId).modulo.alMostrar?.();
}
