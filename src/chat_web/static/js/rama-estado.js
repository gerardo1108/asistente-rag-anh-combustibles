/** Rama "Ver estado". Espejo de src/chat/rama_estado.py. */

import { ApiError, consultarEstado, generarTextoEstado } from "./api-client.js";
import { crearBurbuja, crearBurbujaFormulario } from "./componentes.js";

const DESCRIPCION_ESTADO = {
  REGISTRADO: "Está pendiente de evaluación.",
  APROBADO: "El trámite fue aprobado.",
  RECHAZADO: "El trámite fue rechazado.",
};

const MENSAJE_BIENVENIDA = "Ingresa el código de tu trámite y te diré en qué estado se encuentra.";

export function mostrar(contenedor) {
  contenedor.innerHTML = "";

  // Mismo patrón que el mensaje de bienvenida de "Registrar formulario"
  // (rama-solicitud.js, paso1): esta pestaña no tiene una lista de mensajes
  // propia como "Consultar", así que el saludo va en su propio wrapper,
  // antes del panel del formulario.
  const intro = document.createElement("div");
  intro.className = "mensaje-intro";
  intro.appendChild(crearBurbuja("asistente", MENSAJE_BIENVENIDA));
  contenedor.appendChild(intro);

  const panel = document.createElement("div");
  panel.innerHTML = `
    <div class="panel-formulario">
      <label for="input-codigo">Código de trámite (formato ANH-AAAA-XXXXXX)</label>
      <input type="text" id="input-codigo" placeholder="ANH-2026-000001" />
      <button id="boton-consultar" class="boton-primario">Consultar</button>
    </div>
  `;

  // El formulario se presenta como un turno de chat del usuario; la
  // respuesta (éxito, no encontrado o error) se agrega después como un
  // turno del asistente aparte, no anidada dentro de la burbuja del
  // formulario — mismo contenedor scrolleable que usa "Consultar".
  const mensajes = document.createElement("div");
  mensajes.className = "mensajes";
  mensajes.id = "mensajes-estado";
  mensajes.appendChild(crearBurbujaFormulario(panel.firstElementChild));
  contenedor.appendChild(mensajes);

  contenedor.querySelector("#boton-consultar").addEventListener("click", onConsultar);
}

export function reset() {}

function textoLocalDeRespaldo(estado) {
  let texto = `El trámite **${estado.codigo_tramite}** está **${estado.estado}**. ${DESCRIPCION_ESTADO[estado.estado]}`;
  if (estado.estado === "RECHAZADO" && estado.motivo_rechazo) {
    texto += `\n\nMotivo: ${estado.motivo_rechazo}`;
  }
  return texto;
}

async function onConsultar() {
  const codigo = document.getElementById("input-codigo").value.trim();
  const mensajes = document.getElementById("mensajes-estado");
  // Una sola respuesta visible por consulta: se quita la anterior, si la hay.
  mensajes.querySelector(".resultado-estado")?.remove();
  if (!codigo) return;

  // El resultado se muestra siempre como una única burbuja de respuesta del
  // asistente —éxito, no encontrado o error—, nunca como panel/tarjeta
  // aparte, y sin eco del mensaje del usuario (el input + botón ya dejan
  // clara la acción).
  let texto;
  let modo = "markdown";
  try {
    const estado = await consultarEstado(codigo);
    try {
      // El texto lo redacta un LLM (servicio RAG); si todos los proveedores
      // fallan, ese mismo endpoint ya responde 200 con un texto de
      // respaldo, así que llegar acá al catch solo pasa si el servicio en
      // sí no respondió (red, servicio caído) — ahí cae al compositor
      // local de siempre, segunda capa de resiliencia.
      const resultado = await generarTextoEstado({
        codigo: estado.codigo_tramite,
        estado: estado.estado,
        fecha_registro: estado.fecha_registro,
        motivo_rechazo: estado.motivo_rechazo,
      });
      texto = resultado.texto;
      modo = "strong";
    } catch {
      texto = textoLocalDeRespaldo(estado);
    }
  } catch (error) {
    if (error instanceof ApiError && error.statusCode === 404) {
      texto = "No encontramos ese trámite. Revisá el código e intentá de nuevo.";
    } else {
      texto = error instanceof ApiError ? error.mensaje : "Ocurrió un error inesperado.";
    }
  }
  const fila = crearBurbuja("asistente", texto, { modo });
  fila.classList.add("resultado-estado");
  mensajes.appendChild(fila);
  mensajes.scrollTop = mensajes.scrollHeight;
}
