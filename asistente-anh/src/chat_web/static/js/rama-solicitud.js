/**
 * Rama "Registrar formulario": wizard de 5 pasos. Espejo de
 * src/chat/rama_solicitud.py.
 *
 * Los 5 pasos se acumulan como turnos de chat en un único `.mensajes`
 * scrolleable (mismo contenedor que usa "Consultar"), en vez de reemplazarse
 * uno al otro: cada paso completado queda visible pero congelado (inputs y
 * botones deshabilitados), y el siguiente se agrega debajo. Es estrictamente
 * hacia adelante — no hay botón "atrás" — así que los ids de cada paso no
 * colisionan entre sí aunque el DOM de pasos previos siga montado.
 *
 * A diferencia de la versión Streamlit, los selects en cascada de
 * departamento/provincia/municipio se repueblan de forma normal en el
 * evento `change` del padre — no hace falta el truco de keys dinámicas que
 * se usó ahí para esquivar un bug de reconciliación de widgets propio de
 * Streamlit; en el DOM no existe ese problema.
 */

import { ApiError, registrarSolicitud, validarImagen, verificarCiudadania } from "./api-client.js";
import { VALIDACION_IMAGENES_ACTIVA } from "./config.js";
import { cargarActividades, cargarUbicaciones } from "./catalogos.js";
import { generarUUID } from "./util.js";
import { crearBurbuja, crearBurbujaFormulario } from "./componentes.js";

const MENSAJE_INTRO =
  "Te voy a pedir tu documento de identidad primero, para validarlo contra Ciudadanía Digital antes de continuar.";

const ETIQUETAS_UBICACION = {
  departamento: "Departamento",
  provincia: "Provincia",
  municipio: "Municipio",
  direccion: "Dirección",
};
const ETIQUETAS_CONSUMO = {
  actividad: "Actividad",
  producto: "Producto",
  volumen_litros: "Volumen (litros)",
  uso_destino: "Uso / destino",
};

function estadoInicial() {
  return {
    titular: null,
    campos: null,
    fotoBase64: null,
    fotoNombre: null,
    fotoMime: null,
    idempotencyKey: null,
    resultado: null,
    esDuplicado: false,
  };
}

let estado = estadoInicial();
let contenedorMensajes = null;
let filaPaso2 = null;
let filaPaso3 = null;

export function mostrar(contenedor) {
  contenedor.innerHTML = "";
  contenedorMensajes = document.createElement("div");
  contenedorMensajes.className = "mensajes";
  contenedor.appendChild(contenedorMensajes);

  contenedorMensajes.appendChild(crearBurbuja("asistente", MENSAJE_INTRO));
  agregarPaso1();
}

export function reset() {
  estado = estadoInicial();
  filaPaso2 = null;
  filaPaso3 = null;
}

/** Llamado por estado-app.js cada vez que esta pestaña vuelve a quedar activa. */
export function alMostrar() {
  if (contenedorMensajes) irAlFinal();
}

function irAlFinal() {
  contenedorMensajes.scrollTop = contenedorMensajes.scrollHeight;
}

/** Deja un turno ya completado como registro de chat cerrado: todos sus
 * campos y botones dejan de ser interactivos, en vez de removerse. */
function congelar(nodo) {
  nodo.querySelectorAll("input, select, textarea, button").forEach((el) => {
    el.disabled = true;
  });
}

function descongelar(nodo) {
  nodo.querySelectorAll("input, select, textarea, button").forEach((el) => {
    el.disabled = false;
  });
}

function volverDesde(filaActual, filaAnterior) {
  const mensajeAnterior = filaActual.previousElementSibling;
  filaActual.remove();
  mensajeAnterior?.remove();
  if (filaAnterior) {
    descongelar(filaAnterior.querySelector(".panel-formulario"));
    filaAnterior.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

// --- Paso 1: verificar identidad ---

function agregarPaso1() {
  const panel = document.createElement("div");
  panel.innerHTML = `
    <div class="panel-formulario">
      <label for="input-tipo-doc">Tipo de documento</label>
      <select id="input-tipo-doc">
        <option value="CI">Cédula de Identidad</option>
      </select>
      <label for="input-num-doc">Número de documento</label>
      <input type="text" id="input-num-doc" placeholder="Ej. 1234567" />
      <button id="boton-verificar" class="boton-primario">Verificar identidad</button>
      <div id="mensaje-paso1"></div>
    </div>
  `;
  const nodo = panel.firstElementChild;
  contenedorMensajes.appendChild(crearBurbujaFormulario(nodo));
  irAlFinal();

  nodo.querySelector("#boton-verificar").addEventListener("click", () => onVerificarIdentidad(nodo));
}

async function onVerificarIdentidad(nodo) {
  const tipoDocumento = nodo.querySelector("#input-tipo-doc").value;
  const numeroDocumento = nodo.querySelector("#input-num-doc").value.trim();
  const mensajeDiv = nodo.querySelector("#mensaje-paso1");
  mensajeDiv.innerHTML = "";

  if (!numeroDocumento) {
    mensajeDiv.innerHTML = `<p class="texto-aviso">Ingresá tu número de documento.</p>`;
    return;
  }

  try {
    estado.titular = await verificarCiudadania(tipoDocumento, numeroDocumento);
    congelar(nodo);
    const t = estado.titular;
    contenedorMensajes.appendChild(
      crearBurbuja("asistente", `¡Listo, ${t.nombres} ${t.primer_apellido}! Verificamos tu identidad. Ahora necesito los datos del consumo que vas a registrar.`),
    );
    irAlFinal();
    await agregarPaso2();
  } catch (error) {
    if (error instanceof ApiError && error.statusCode === 404) {
      mensajeDiv.innerHTML =
        `<p class="texto-aviso">No encontramos tu registro en Ciudadanía Digital. ` +
        `Registrate ahí primero y vuelve a intentarlo.</p>`;
    } else {
      const mensaje = error instanceof ApiError ? error.mensaje : "Ocurrió un error inesperado.";
      mensajeDiv.innerHTML = `<p class="texto-error">${mensaje}</p>`;
    }
  }
}

// --- Paso 2: datos del consumo ---

/** `placeholder`: si se da, agrega una opción vacía deshabilitada/seleccionada
 * primero ("Elegir..."), para que el select no arranque en la primera opción
 * real como si ya fuera un dato cargado. */
function llenarSelect(select, opciones, { placeholder = null } = {}) {
  select.innerHTML = "";
  if (placeholder) {
    const opcionVacia = document.createElement("option");
    opcionVacia.value = "";
    opcionVacia.textContent = placeholder;
    opcionVacia.disabled = true;
    opcionVacia.selected = true;
    select.appendChild(opcionVacia);
  }
  for (const opcion of opciones) {
    const item = document.createElement("option");
    item.value = opcion;
    item.textContent = opcion;
    select.appendChild(item);
  }
}

async function agregarPaso2() {
  const ubicaciones = await cargarUbicaciones();
  const actividades = await cargarActividades();
  const titular = estado.titular;

  const panel = document.createElement("div");
  panel.innerHTML = `
    <div class="panel-formulario">
      <label for="input-correo-paso2">Correo</label>
      <input type="text" id="input-correo-paso2" value="${titular.correo ?? ""}" readonly />
      <label for="input-celular-paso2">Celular</label>
      <input type="text" id="input-celular-paso2" value="${titular.celular ?? ""}" readonly />
      <label for="sel-departamento">Departamento</label>
      <select id="sel-departamento"></select>
      <label for="sel-provincia">Provincia</label>
      <select id="sel-provincia"></select>
      <label for="sel-municipio">Municipio</label>
      <select id="sel-municipio"></select>
      <label for="input-direccion">Dirección</label>
      <input type="text" id="input-direccion" />
      <label for="sel-actividad">Actividad</label>
      <select id="sel-actividad"></select>
      <label for="sel-producto">Producto</label>
      <select id="sel-producto"></select>
      <label for="input-volumen">Volumen (litros)</label>
      <input type="number" id="input-volumen" min="0" step="1" />
      <div id="mensaje-volumen"></div>
      <label for="input-uso">Uso / destino del combustible</label>
      <textarea id="input-uso"></textarea>
      <button id="boton-continuar-paso2" class="boton-primario">Continuar</button>
      <div id="mensaje-paso2"></div>
    </div>
  `;
  const nodo = panel.firstElementChild;
  filaPaso2 = crearBurbujaFormulario(nodo);
  contenedorMensajes.appendChild(filaPaso2);
  irAlFinal();

  const selDepartamento = nodo.querySelector("#sel-departamento");
  const selProvincia = nodo.querySelector("#sel-provincia");
  const selMunicipio = nodo.querySelector("#sel-municipio");
  const inputVolumen = nodo.querySelector("#input-volumen");
  const mensajeVolumenDiv = nodo.querySelector("#mensaje-volumen");
  let maximoLitros = null;

  llenarSelect(selDepartamento, Object.keys(ubicaciones), { placeholder: "Elegir..." });
  llenarSelect(nodo.querySelector("#sel-actividad"), actividades, { placeholder: "Elegir..." });
  llenarSelect(nodo.querySelector("#sel-producto"), ["DIESEL", "GASOLINA"], { placeholder: "Elegir..." });

  const repoblarMunicipios = () => {
    const departamento = selDepartamento.value;
    const provincia = selProvincia.value;
    if (!departamento || !provincia) {
      llenarSelect(selMunicipio, [], { placeholder: "Elegir..." });
      return;
    }
    llenarSelect(selMunicipio, Object.keys(ubicaciones[departamento][provincia]), { placeholder: "Elegir..." });
  };
  const actualizarLimiteVolumen = () => {
    const municipio = ubicaciones[selDepartamento.value]?.[selProvincia.value]?.[selMunicipio.value];
    if (!municipio) {
      maximoLitros = null;
      inputVolumen.removeAttribute("max");
      mensajeVolumenDiv.innerHTML = "";
      return;
    }
    maximoLitros = municipio.es_frontera ? 50 : 120;
    inputVolumen.max = String(maximoLitros);
    mensajeVolumenDiv.innerHTML = `<p class="texto-aviso">Límite aplicable: ${maximoLitros} litros.</p>`;
    validarVolumen();
  };
  const validarVolumen = () => {
    const valor = parseFloat(inputVolumen.value);
    if (maximoLitros !== null && valor > maximoLitros) {
      mensajeVolumenDiv.innerHTML = `<p class="texto-error">El volumen no puede superar los ${maximoLitros} litros.</p>`;
      return false;
    }
    if (maximoLitros !== null) {
      mensajeVolumenDiv.innerHTML = `<p class="texto-aviso">Límite aplicable: ${maximoLitros} litros.</p>`;
    }
    return true;
  };
  const repoblarProvincias = () => {
    const departamento = selDepartamento.value;
    if (!departamento) {
      llenarSelect(selProvincia, [], { placeholder: "Elegir..." });
      repoblarMunicipios();
      return;
    }
    llenarSelect(selProvincia, Object.keys(ubicaciones[departamento]), { placeholder: "Elegir..." });
    repoblarMunicipios();
  };

  selDepartamento.addEventListener("change", repoblarProvincias);
  selProvincia.addEventListener("change", repoblarMunicipios);
  selMunicipio.addEventListener("change", actualizarLimiteVolumen);
  inputVolumen.addEventListener("input", validarVolumen);
  repoblarProvincias();

  nodo.querySelector("#boton-continuar-paso2").addEventListener("click", () => {
    const departamento = selDepartamento.value;
    const provincia = selProvincia.value;
    const municipio = selMunicipio.value;
    const direccion = nodo.querySelector("#input-direccion").value.trim();
    const actividad = nodo.querySelector("#sel-actividad").value;
    const producto = nodo.querySelector("#sel-producto").value;
    const volumenLitros = parseFloat(nodo.querySelector("#input-volumen").value);
    const usoDestino = nodo.querySelector("#input-uso").value.trim();
    const mensajeDiv = nodo.querySelector("#mensaje-paso2");

    if (
      !departamento ||
      !provincia ||
      !municipio ||
      !actividad ||
      !producto ||
      !direccion ||
      !usoDestino ||
      !(volumenLitros > 0)
    ) {
      mensajeDiv.innerHTML =
        `<p class="texto-aviso">Completá todos los desplegables, dirección y uso/destino, y el volumen debe ser mayor a cero.</p>`;
      return;
    }
    if (!validarVolumen()) return;

    estado.campos = {
      departamento,
      provincia,
      municipio,
      direccion,
      actividad,
      producto,
      volumen_litros: volumenLitros,
      uso_destino: usoDestino,
    };
    congelar(nodo);
    contenedorMensajes.appendChild(
      crearBurbuja(
        "asistente",
        "Perfecto, ya registré los datos del consumo. Ahora necesito una fotografía tuya sosteniendo tu documento de identidad.",
      ),
    );
    irAlFinal();
    agregarPaso3();
  });
}

// --- Paso 3: foto ---

function leerComoDataUrl(archivo) {
  return new Promise((resolve, reject) => {
    const lector = new FileReader();
    lector.onload = () => resolve(lector.result);
    lector.onerror = () => reject(lector.error);
    lector.readAsDataURL(archivo);
  });
}

function formatearTamano(bytes) {
  const mb = bytes / (1024 * 1024);
  if (mb >= 0.1) return `${mb.toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

const SVG_SUBIR =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
  '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>' +
  '<polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>';
const SVG_IMAGEN =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
  '<rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle>' +
  '<path d="M21 15l-5-5L5 21"></path></svg>';
const SVG_BASURERO =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
  '<polyline points="3 6 5 6 21 6"></polyline>' +
  '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path>' +
  '<path d="M10 11v6"></path><path d="M14 11v6"></path>' +
  '<path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"></path></svg>';

function agregarPaso3() {
  const panel = document.createElement("div");
  panel.innerHTML = `
    <div class="panel-formulario">
      <input type="file" id="input-foto" accept=".jpg,.jpeg,.png" hidden />
      <div class="fila-adjuntar-foto">
        <button type="button" id="boton-adjuntar-foto" class="boton-adjuntar-foto">${SVG_SUBIR} Adjuntar foto</button>
        <button type="button" id="boton-quitar-foto" class="boton-quitar-foto oculto" title="Quitar foto">${SVG_BASURERO}</button>
      </div>
      <div id="confirmacion-foto" class="confirmacion-foto oculto">
        <div class="icono-archivo">${SVG_IMAGEN}</div>
        <p class="nombre-archivo"></p>
        <p class="tamano-archivo"></p>
      </div>
      <button type="button" id="boton-regresar-paso3" class="boton-secundario">Volver al paso anterior</button>
      <button id="boton-continuar-paso3" class="boton-primario boton-ancho-completo" disabled>Continuar</button>
      <div id="mensaje-paso3"></div>
    </div>
  `;
  const nodo = panel.firstElementChild;
  filaPaso3 = crearBurbujaFormulario(nodo);
  contenedorMensajes.appendChild(filaPaso3);
  irAlFinal();

  const inputFoto = nodo.querySelector("#input-foto");
  const botonAdjuntar = nodo.querySelector("#boton-adjuntar-foto");
  const botonQuitar = nodo.querySelector("#boton-quitar-foto");
  const confirmacion = nodo.querySelector("#confirmacion-foto");
  const iconoArchivo = nodo.querySelector(".icono-archivo");
  const boton = nodo.querySelector("#boton-continuar-paso3");

  nodo.querySelector("#boton-regresar-paso3").addEventListener("click", () => {
    volverDesde(filaPaso3, filaPaso2);
    filaPaso3 = null;
  });

  let urlPreviaFoto = null;

  botonAdjuntar.addEventListener("click", () => inputFoto.click());

  botonQuitar.addEventListener("click", () => {
    inputFoto.value = "";
    if (urlPreviaFoto) {
      URL.revokeObjectURL(urlPreviaFoto);
      urlPreviaFoto = null;
    }
    iconoArchivo.innerHTML = SVG_IMAGEN;
    confirmacion.classList.add("oculto");
    botonQuitar.classList.add("oculto");
    boton.disabled = true;
  });

  inputFoto.addEventListener("change", () => {
    const archivo = inputFoto.files[0];
    boton.disabled = !archivo;
    confirmacion.classList.toggle("oculto", !archivo);
    botonQuitar.classList.toggle("oculto", !archivo);
    if (archivo) {
      if (urlPreviaFoto) URL.revokeObjectURL(urlPreviaFoto);
      urlPreviaFoto = URL.createObjectURL(archivo);
      iconoArchivo.innerHTML = `<img src="${urlPreviaFoto}" alt="" />`;
      confirmacion.querySelector(".nombre-archivo").textContent = archivo.name;
      confirmacion.querySelector(".tamano-archivo").innerHTML = `✓ ${formatearTamano(archivo.size)}`;
    }
  });

  boton.addEventListener("click", async () => {
    const archivo = inputFoto.files[0];
    if (!archivo) return;
    const dataUrl = await leerComoDataUrl(archivo);
    estado.fotoBase64 = dataUrl.split(",")[1];
    estado.fotoNombre = archivo.name;
    estado.fotoMime = archivo.type || "image/jpeg";
    if (VALIDACION_IMAGENES_ACTIVA) {
      boton.disabled = true;
      try {
        const resultado = await validarImagen(estado.fotoBase64, estado.fotoMime, estado.fotoNombre);
        if (resultado.veredicto !== "VALIDA") {
          nodo.querySelector("#mensaje-paso3").innerHTML = `<p class="texto-error">${resultado.motivo || "La imagen no cumple los requisitos."}</p>`;
          boton.disabled = false;
          return;
        }
      } catch (error) {
        const mensaje = error instanceof ApiError ? error.mensaje : "No se pudo validar la imagen.";
        nodo.querySelector("#mensaje-paso3").innerHTML = `<p class="texto-error">${mensaje}</p>`;
        boton.disabled = false;
        return;
      }
    }
    congelar(nodo);
    contenedorMensajes.appendChild(
      crearBurbuja("asistente", "Gracias, recibí tu foto. Antes de enviar tu solicitud, revisá que los datos estén correctos."),
    );
    irAlFinal();
    agregarPaso4();
  });
}

// --- Paso 4: resumen + envío ---

function armarSobre() {
  const t = estado.titular;
  return {
    tramite: "ANH-REGISTRO-CONSUMO-FUERA-TANQUE",
    version_formulario: "1.0",
    canal_origen: "ASISTENTE_CONVERSACIONAL",
    solicitante: {
      tipo_documento: t.tipo_documento,
      numero_documento: t.numero_documento,
      nombres: t.nombres,
      primer_apellido: t.primer_apellido,
      segundo_apellido: t.segundo_apellido ?? null,
      correo: t.correo ?? null,
      celular: t.celular ?? null,
    },
    datos: Object.entries(estado.campos).map(([campo, valor]) => ({ campo, valor })),
    adjuntos: [
      {
        tipo: "FOTO_TITULAR_CON_CI",
        nombre_archivo: estado.fotoNombre,
        mime: estado.fotoMime,
        contenido_base64: estado.fotoBase64,
      },
    ],
    declaracion_jurada: true,
  };
}

function agregarPaso4() {
  const t = estado.titular;
  const c = estado.campos;
  const filasUbicacion = Object.entries(ETIQUETAS_UBICACION)
    .map(([clave, etiqueta]) => `<p><strong>${etiqueta}:</strong> ${c[clave]}</p>`)
    .join("");
  const filasConsumo = Object.entries(ETIQUETAS_CONSUMO)
    .map(([clave, etiqueta]) => `<p><strong>${etiqueta}:</strong> ${c[clave]}</p>`)
    .join("");

  const panel = document.createElement("div");
  panel.innerHTML = `
    <div class="panel-formulario">
      <div class="grupo-revision">
        <p><strong>Titular:</strong> ${t.nombres} ${t.primer_apellido} ${t.segundo_apellido ?? ""}</p>
        <p><strong>Documento:</strong> ${t.tipo_documento} ${t.numero_documento}</p>
        <p><strong>Correo:</strong> ${t.correo ?? ""}</p>
        <p><strong>Celular:</strong> ${t.celular ?? ""}</p>
      </div>
      <hr class="separador-revision" />
      <div class="grupo-revision">
        ${filasUbicacion}
      </div>
      <hr class="separador-revision" />
      <div class="grupo-revision">
        ${filasConsumo}
      </div>
      <hr class="separador-revision" />
      <p><strong>Foto:</strong></p>
      <img class="foto-previa" src="data:${estado.fotoMime};base64,${estado.fotoBase64}" alt="Foto del titular con su documento de identidad" />
      <label class="checkbox">
        <input type="checkbox" id="input-jurada" />
        Declaro que la información proporcionada es verídica y asumo responsabilidad por su veracidad,
        conforme a la normativa vigente.
      </label>
      <button type="button" id="boton-regresar-paso4" class="boton-secundario">Volver al paso anterior</button>
      <button id="boton-enviar" class="boton-primario boton-ancho-completo" disabled>Confirmar y enviar</button>
      <div id="mensaje-paso4"></div>
    </div>
  `;
  const nodo = panel.firstElementChild;
  const filaPaso4 = crearBurbujaFormulario(nodo);
  contenedorMensajes.appendChild(filaPaso4);
  irAlFinal();

  const checkbox = nodo.querySelector("#input-jurada");
  const boton = nodo.querySelector("#boton-enviar");
  nodo.querySelector("#boton-regresar-paso4").addEventListener("click", () => {
    volverDesde(filaPaso4, filaPaso3);
  });
  checkbox.addEventListener("change", () => {
    boton.disabled = !checkbox.checked;
  });

  boton.addEventListener("click", async () => {
    const mensajeDiv = nodo.querySelector("#mensaje-paso4");
    mensajeDiv.innerHTML = "";
    // Se genera una sola vez por intento de envío: los reintentos ante un
    // error de red reusan la misma clave para no duplicar el trámite.
    if (!estado.idempotencyKey) {
      estado.idempotencyKey = generarUUID();
    }
    boton.disabled = true;

    try {
      const { body, esDuplicado } = await registrarSolicitud(armarSobre(), estado.idempotencyKey);
      estado.resultado = body;
      estado.esDuplicado = esDuplicado;
      congelar(nodo);
      agregarPaso5();
    } catch (error) {
      const mensaje = error instanceof ApiError ? error.mensaje : "Ocurrió un error inesperado.";
      mensajeDiv.innerHTML = `<p class="texto-error">${mensaje}</p>`;
      boton.disabled = false;
    }
  });
}

// --- Paso 5: resultado ---

/** A diferencia de los pasos 1-4 (turnos del usuario), el resultado final es
 * información que el sistema le comunica al usuario — mismo criterio que ya
 * usa "Ver estado" para su respuesta: burbuja del asistente, no un
 * formulario más. */
function agregarPaso5() {
  const r = estado.resultado;
  const intro = estado.esDuplicado
    ? "Esta solicitud ya había sido registrada antes; este es tu código de trámite."
    : "¡Solicitud registrada!";
  const texto =
    `${intro}\n\n` +
    `Tu código de trámite es **${r.codigo_tramite}**.\n\n` +
    `Guardá este código: lo vas a necesitar para consultar el estado de tu trámite.`;

  contenedorMensajes.appendChild(crearBurbuja("asistente", texto));
  irAlFinal();
}
