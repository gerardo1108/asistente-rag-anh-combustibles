import { markdownBasicoAHtml, permitirSoloStrong } from "./markdown.js";

const SVG_CHISPA =
  '<svg class="avatar-icono" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true">' +
  '<path d="M12 2L14 10L22 12L14 14L12 22L10 14L2 12L10 10Z"/></svg>';
const SVG_PERSONA =
  '<svg class="avatar-icono" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true">' +
  '<circle cx="12" cy="8" r="4"></circle><path d="M4 20a8 8 0 0 1 16 0z"></path></svg>';
const SVG_CHEVRON_VOLVER =
  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3F3F3A" stroke-width="2.5" ' +
  'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"></polyline></svg>';

/**
 * Construye una fila de mensaje de chat (burbuja + hora + avatar, uno de
 * cada lado). `modo`: "markdown" (default, **negrita**, usado por
 * "Consultar"), "strong" (permite <strong> literal, usado por "Ver estado"
 * con el texto que arma el LLM), o "html" (el texto ya viene armado como
 * HTML seguro por el llamador -p. ej. el bloque de Nota/Fuentes de
 * "Consultar"-, se inserta tal cual, sin pasar por ningún escape acá).
 */
export function crearBurbuja(rol, texto, { modo = "markdown" } = {}) {
  const fila = document.createElement("div");
  fila.className = `mensaje mensaje-${rol}`;

  const avatar = document.createElement("div");
  avatar.className = `avatar avatar-${rol}`;
  avatar.innerHTML = rol === "asistente" ? SVG_CHISPA : SVG_PERSONA;
  fila.appendChild(avatar);

  const columna = document.createElement("div");
  columna.className = "mensaje-columna";

  const burbuja = document.createElement("div");
  burbuja.className = "burbuja";
  if (modo === "html") {
    burbuja.innerHTML = texto;
  } else {
    burbuja.innerHTML = modo === "strong" ? permitirSoloStrong(texto) : markdownBasicoAHtml(texto);
  }
  columna.appendChild(burbuja);

  const hora = document.createElement("span");
  hora.className = "hora";
  hora.textContent = new Date().toLocaleTimeString("es-BO", { hour: "2-digit", minute: "2-digit" });
  columna.appendChild(hora);

  fila.appendChild(columna);
  return fila;
}

/**
 * Envuelve un panel de formulario (p. ej. el paso 1 de "Registrar
 * formulario" o el input de código de "Ver estado") como un turno de chat
 * del usuario: misma fila avatar+burbuja que `crearBurbuja`, pero con el
 * contenido del formulario adentro en vez de texto, para que quede alineado
 * a la derecha con el resto de los mensajes del usuario.
 */
export function crearBurbujaFormulario(nodoContenido) {
  const fila = document.createElement("div");
  fila.className = "mensaje mensaje-usuario mensaje-formulario";

  const avatar = document.createElement("div");
  avatar.className = "avatar avatar-usuario";
  avatar.innerHTML = SVG_PERSONA;
  fila.appendChild(avatar);

  const columna = document.createElement("div");
  columna.className = "mensaje-columna";

  const burbuja = document.createElement("div");
  burbuja.className = "burbuja burbuja-formulario";
  burbuja.appendChild(nodoContenido);
  columna.appendChild(burbuja);

  const hora = document.createElement("span");
  hora.className = "hora";
  hora.textContent = new Date().toLocaleTimeString("es-BO", { hour: "2-digit", minute: "2-digit" });
  columna.appendChild(hora);

  fila.appendChild(columna);
  return fila;
}

/**
 * Burbuja de asistente que introduce un paso del wizard de "Registrar
 * formulario": encabezado "PASO {numero} · {etiqueta}" en naranja, seguido
 * de una breve descripción. Si se da `onVolver`, agrega un botón circular
 * en la esquina superior derecha de la burbuja para volver al paso anterior
 * (usado en los pasos 2, 3 y 4; nunca en el 1 ni en el 5).
 */
export function crearBurbujaPaso(numero, etiqueta, descripcion, { modo = "markdown", onVolver } = {}) {
  const descripcionHtml =
    modo === "strong" ? permitirSoloStrong(descripcion) : markdownBasicoAHtml(descripcion);
  const html =
    `<div class="encabezado-paso"><span class="etiqueta-paso">PASO ${numero} · ${etiqueta}</span></div>` +
    `<p class="descripcion-paso">${descripcionHtml}</p>`;
  const fila = crearBurbuja("asistente", html, { modo: "html" });
  const burbuja = fila.querySelector(".burbuja");
  burbuja.classList.add("burbuja-paso");

  if (onVolver) {
    burbuja.classList.add("burbuja-paso--con-volver");
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "boton-volver-paso";
    boton.title = "Volver al paso anterior";
    boton.setAttribute("aria-label", "Volver al paso anterior");
    boton.innerHTML = `${SVG_CHEVRON_VOLVER}<span>Volver</span>`;
    boton.addEventListener("click", onVolver);
    burbuja.appendChild(boton);
  }

  return fila;
}

/**
 * `variante: "error"` se usa para la advertencia de un fallo transitorio de
 * los proveedores de LLM (ver rag_core.py, campo `advertencia`) — mismo
 * lugar y formato que el caption normal ("Respondido por X en Y ms"), en
 * rojo, para distinguirla de una nota informativa.
 */
export function crearCaption(texto, { variante } = {}) {
  const caption = document.createElement("p");
  caption.className = variante ? `caption caption--${variante}` : "caption";
  caption.textContent = texto;
  return caption;
}
