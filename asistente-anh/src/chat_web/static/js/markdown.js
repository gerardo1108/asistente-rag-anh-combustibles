/**
 * Conversión mínima de markdown a HTML: solo negrita (**texto**). No es un
 * parser de markdown completo — cubre lo que efectivamente devuelve el RAG
 * (el resto, como listas con "- " o "1. ", ya se lee bien como texto plano
 * con los saltos de línea que preserva `white-space: pre-line` en el CSS).
 * Escapa HTML antes de aplicar el formato, para no interpretar como markup
 * nada que venga en el texto de la respuesta.
 */
export function escaparHtml(texto) {
  return texto.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function markdownBasicoAHtml(texto) {
  return escaparHtml(texto).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

/**
 * Como `markdownBasicoAHtml`, pero para texto que puede traer `<strong>`
 * literal en vez de `**negrita**` (el LLM de "Ver estado" lo usa así, por
 * instrucción del prompt). Escapa todo el HTML primero -igual que la otra
 * función- y solo "desescapa" `<strong>`/`</strong>`: es un allowlist de una
 * sola etiqueta, no HTML crudo. Cualquier otro contenido (incluido algo que
 * venga de un motivo de rechazo cargado por un supervisor) queda inerte.
 */
export function permitirSoloStrong(texto) {
  return escaparHtml(texto).replace(/&lt;strong&gt;/g, "<strong>").replace(/&lt;\/strong&gt;/g, "</strong>");
}
