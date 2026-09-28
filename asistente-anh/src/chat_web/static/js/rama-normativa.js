/** Rama "Consultar". Espejo de src/chat/rama_normativa.py. */

import { ApiError, consultarRag } from "./api-client.js";
import { crearBurbuja, crearCaption } from "./componentes.js";
import { escaparHtml, markdownBasicoAHtml } from "./markdown.js";

const SVG_ENVIAR =
  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" ' +
  'stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"></line>' +
  '<polyline points="6 11 12 5 18 11"></polyline></svg>';

const MENSAJE_BIENVENIDA =
  "¡Hola! Soy el Asistente ANH. Puedo ayudarte con preguntas sobre la normativa y el procedimiento para registrar tu consumo de combustibles líquidos fuera de tanque. ¿En qué te puedo ayudar?";

/**
 * El aviso "orientativa" ya lo arma el LLM dentro de `resultado.respuesta`
 * (instrucción del prompt en rag_core.py) — no se agrega uno propio del
 * frontend, para no duplicarlo.
 */
function construirHtmlRespuesta(resultado) {
  let html = markdownBasicoAHtml(resultado.respuesta);
  if (resultado.encontrado && resultado.fuentes?.length) {
    html += `<hr class="separador" />`;
    const items = resultado.fuentes
      .map((f) => `- ${escaparHtml(f.norma)}, ${escaparHtml(f.articulo)}`)
      .join("<br>");
    html += `<div class="fuentes"><strong>Fuentes:</strong><br>${items}</div>`;
  }
  return html;
}

export function mostrar(contenedor) {
  contenedor.innerHTML = `
    <div class="mensajes" id="mensajes"></div>
    <form class="chat-input" id="form-pregunta">
      <input type="text" id="input-pregunta" placeholder="Escribe tu pregunta sobre el trámite..." autocomplete="off" />
      <button type="submit" aria-label="Enviar">${SVG_ENVIAR}</button>
    </form>
  `;
  // Primer elemento de la lista de mensajes, siempre presente al entrar o
  // reiniciar esta pestaña (mostrar() se reconstruye entera en ambos casos).
  document.getElementById("mensajes").appendChild(crearBurbuja("asistente", MENSAJE_BIENVENIDA));
  contenedor.querySelector("#form-pregunta").addEventListener("submit", onEnviar);
}

let preguntaAnterior = null;

/** Llamado por estado-app.js cada vez que esta pestaña vuelve a quedar activa. */
export function alMostrar() {
  const mensajes = document.getElementById("mensajes");
  if (mensajes) irAlFinal(mensajes);
}

export function reset() {
  preguntaAnterior = null;
}

function irAlFinal(mensajes) {
  mensajes.scrollTop = mensajes.scrollHeight;
}

async function onEnviar(evento) {
  evento.preventDefault();
  const input = document.getElementById("input-pregunta");
  const pregunta = input.value.trim();
  if (!pregunta) return;
  input.value = "";

  const mensajes = document.getElementById("mensajes");
  // El historial se acumula (no se reemplaza): la pestaña mantiene su
  // estado al cambiar a otra y volver, así que puede haber muchos
  // intercambios — el área de mensajes scrollea internamente, ver estilos.css.
  mensajes.appendChild(crearBurbuja("usuario", pregunta));
  irAlFinal(mensajes);

  const contexto = preguntaAnterior ? `El usuario preguntó antes: "${preguntaAnterior}"` : undefined;
  preguntaAnterior = pregunta;

  try {
    const resultado = await consultarRag(pregunta, contexto);
    mensajes.appendChild(crearBurbuja("asistente", construirHtmlRespuesta(resultado), { modo: "html" }));
    if (resultado.proveedor_llm && resultado.tiempo_respuesta_ms != null) {
      mensajes.appendChild(crearCaption(`Respondido por ${resultado.proveedor_llm} en ${resultado.tiempo_respuesta_ms} ms`));
    }
  } catch (error) {
    const mensaje = error instanceof ApiError ? error.mensaje : "Ocurrió un error inesperado.";
    mensajes.appendChild(crearBurbuja("asistente", mensaje));
  }
  irAlFinal(mensajes);
}
