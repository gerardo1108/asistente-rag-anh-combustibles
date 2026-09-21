import { markdownBasicoAHtml, permitirSoloStrong } from "./markdown.js";

const SVG_CHISPA =
  '<svg class="avatar-icono" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true">' +
  '<path d="M12 2L14 10L22 12L14 14L12 22L10 14L2 12L10 10Z"/></svg>';
const SVG_PERSONA =
  '<svg class="avatar-icono" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true">' +
  '<circle cx="12" cy="8" r="4"></circle><path d="M4 20a8 8 0 0 1 16 0z"></path></svg>';

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

export function crearCaption(texto) {
  const caption = document.createElement("p");
  caption.className = "caption";
  caption.textContent = texto;
  return caption;
}
