/**
 * Rama "Registrar formulario": wizard de 5 pasos. Espejo de
 * src/chat/rama_solicitud.py.
 *
 * Los 5 pasos se acumulan como turnos de chat en un único `.mensajes`
 * scrolleable (mismo contenedor que usa "Consultar"), en vez de reemplazarse
 * uno al otro: cada paso completado queda visible pero congelado (inputs y
 * botones deshabilitados), y el siguiente se agrega debajo.
 *
 * Los pasos 2, 3 y 4 tienen un botón "volver" en su burbuja de introducción
 * (`crearBurbujaPaso`) que permite reconstruir el paso anterior de forma
 * editable y precargada con los datos ya ingresados — `estado` nunca se
 * limpia entre pasos, así que sirve como fuente de precarga sin necesitar un
 * "modo edición" separado. `pasoActivo` referencia los nodos del paso
 * interactivo actual; `historialPasos` es una pila con los pasos previos ya
 * congelados. Al volver (`volverAPaso`) se remueven del DOM ambos pasos (el
 * actual y el anterior) y se reinvoca `agregarPasoN` desde cero — no existe
 * una función "descongelar", así que reconstruir es más simple y robusto que
 * revertir el `congelar()`. Como el nodo del paso anterior se remueve antes
 * de reconstruirlo, nunca coexisten dos elementos con el mismo id.
 *
 * A diferencia de la versión Streamlit, los selects en cascada de
 * departamento/provincia/municipio se repueblan de forma normal en el
 * evento `change` del padre — no hace falta el truco de keys dinámicas que
 * se usó ahí para esquivar un bug de reconciliación de widgets propio de
 * Streamlit; en el DOM no existe ese problema.
 */

import { ApiError, registrarSolicitud, validarImagenTitular, verificarCiudadania } from "./api-client.js";
import { cargarActividades, cargarUbicaciones } from "./catalogos.js";
import { LITROS_MAXIMO_FRONTERA, LITROS_MAXIMO_NO_FRONTERA } from "./config.js";
import { generarUUID } from "./util.js";
import { crearBurbujaFormulario, crearBurbujaPaso } from "./componentes.js";

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

// Paso interactivo actual: { numero, nodoIntro, nodoFormulario }. `null`
// cuando no hay ningún paso editable montado (antes de mostrar() y después
// de llegar al Paso 5, que es terminal).
let pasoActivo = null;
// Pila de pasos previos ya congelados, para poder removerlos del DOM al
// volver (ver `volverAPaso`).
const historialPasos = [];

export function mostrar(contenedor) {
  contenedor.innerHTML = "";
  contenedorMensajes = document.createElement("div");
  contenedorMensajes.className = "mensajes";
  contenedor.appendChild(contenedorMensajes);

  irAPaso1();
}

export function reset() {
  estado = estadoInicial();
  pasoActivo = null;
  historialPasos.length = 0;
}

/** Agrega la burbuja de introducción "PASO N · ETIQUETA" + descripción, y
 * llama a `agregarFn` para construir el panel de ese paso. Reemplaza el
 * patrón repetido "burbuja de transición + agregarPasoN": se usa tanto para
 * avanzar como, indirectamente, para reconstruir un paso al volver (ver
 * `RECONSTRUCTORES`). Si ya había un paso activo, lo archiva en
 * `historialPasos` antes de reemplazarlo. */
async function avanzarAPaso(numero, etiqueta, descripcion, agregarFn, { onVolver } = {}) {
  if (pasoActivo) {
    // El botón "volver" solo debe mostrarse en el paso activo: `congelar()`
    // deshabilita el panel del formulario, pero la burbuja de introducción
    // (con su propio botón) es un nodo aparte que no toca, así que hay que
    // quitarle el botón acá, en el momento en que este paso deja de ser el
    // actual.
    pasoActivo.nodoIntro.querySelector(".boton-volver-paso")?.remove();
    historialPasos.push(pasoActivo);
  }
  const nodoIntro = crearBurbujaPaso(numero, etiqueta, descripcion, { onVolver });
  contenedorMensajes.appendChild(nodoIntro);
  irAlFinal();
  pasoActivo = { numero, nodoIntro, nodoFormulario: null };
  await agregarFn();
}

function irAPaso1() {
  return avanzarAPaso(1, "IDENTIDAD", MENSAJE_INTRO, agregarPaso1);
}

function irAPaso2() {
  const t = estado.titular;
  return avanzarAPaso(
    2,
    "CONSUMO",
    `¡Listo, ${t.nombres} ${t.primer_apellido}! Verificamos tu identidad. Ahora necesito los datos del consumo que vas a registrar.`,
    agregarPaso2,
    { onVolver: () => volverAPaso(1) },
  );
}

function irAPaso3() {
  return avanzarAPaso(
    3,
    "FOTO",
    "Perfecto, ya registré los datos del consumo. Ahora necesito una fotografía tuya sosteniendo tu documento de identidad.",
    agregarPaso3,
    { onVolver: () => volverAPaso(2) },
  );
}

function irAPaso4() {
  return avanzarAPaso(
    4,
    "RESUMEN",
    "Gracias, recibí tu foto. Antes de enviar tu solicitud, revisá que los datos estén correctos.",
    agregarPaso4,
    { onVolver: () => volverAPaso(3) },
  );
}

const RECONSTRUCTORES = { 1: irAPaso1, 2: irAPaso2, 3: irAPaso3 };

/** Borra del DOM el paso actual y el paso anterior (ambos: intro + panel), y
 * reconstruye el paso anterior desde cero, editable y precargado con los
 * datos que ya tenía en `estado`. */
function volverAPaso(numero) {
  pasoActivo.nodoIntro.remove();
  pasoActivo.nodoFormulario.remove();

  const anterior = historialPasos.pop();
  anterior.nodoIntro.remove();
  anterior.nodoFormulario.remove();

  pasoActivo = null;
  RECONSTRUCTORES[numero]();
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

/** `estado` nunca se limpia solo — es lo que permite precargar un paso al
 * volver a él. Pero eso significa que, al avanzar de nuevo hacia adelante
 * después de un "volver" (con o sin cambios), los pasos posteriores no deben
 * heredar datos de un recorrido anterior: cada uno de estos se llama al
 * confirmar el paso correspondiente, justo antes de avanzar, para que todo
 * lo que venga después arranque en blanco. Se encadenan porque limpiar un
 * paso implica limpiar también todo lo que depende de él. */
function limpiarDesdeConsumo() {
  estado.campos = null;
  limpiarDesdeFoto();
}
function limpiarDesdeFoto() {
  estado.fotoBase64 = null;
  estado.fotoNombre = null;
  estado.fotoMime = null;
  limpiarDesdeEnvio();
}
function limpiarDesdeEnvio() {
  estado.idempotencyKey = null;
  estado.resultado = null;
  estado.esDuplicado = false;
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
  const filaFormulario = crearBurbujaFormulario(nodo);
  contenedorMensajes.appendChild(filaFormulario);
  pasoActivo.nodoFormulario = filaFormulario;
  irAlFinal();

  if (estado.titular) {
    nodo.querySelector("#input-tipo-doc").value = estado.titular.tipo_documento;
    nodo.querySelector("#input-num-doc").value = estado.titular.numero_documento;
  }

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
    limpiarDesdeConsumo();
    congelar(nodo);
    await irAPaso2();
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
  const filaFormulario = crearBurbujaFormulario(nodo);
  contenedorMensajes.appendChild(filaFormulario);
  pasoActivo.nodoFormulario = filaFormulario;
  irAlFinal();

  const selDepartamento = nodo.querySelector("#sel-departamento");
  const selProvincia = nodo.querySelector("#sel-provincia");
  const selMunicipio = nodo.querySelector("#sel-municipio");
  const inputVolumen = nodo.querySelector("#input-volumen");
  const mensajeVolumenDiv = nodo.querySelector("#mensaje-volumen");

  llenarSelect(selDepartamento, Object.keys(ubicaciones), { placeholder: "Elegir..." });
  llenarSelect(nodo.querySelector("#sel-actividad"), actividades, { placeholder: "Elegir..." });
  llenarSelect(nodo.querySelector("#sel-producto"), ["DIESEL", "GASOLINA"], { placeholder: "Elegir..." });

  // Cupo máximo según si el municipio elegido está en zona fronteriza
  // (catalogos/ubicaciones.json, flag `es_frontera`). `null` mientras no hay
  // municipio seleccionado: sin tope, sin placeholder.
  let maximoLitros = null;

  const validarVolumen = () => {
    const valor = parseFloat(inputVolumen.value);
    if (maximoLitros != null && valor > maximoLitros) {
      mensajeVolumenDiv.innerHTML = `<p class="texto-error">El volumen no puede superar los ${maximoLitros} litros.</p>`;
    } else {
      mensajeVolumenDiv.innerHTML = "";
    }
  };

  const actualizarLimiteVolumen = () => {
    const municipio = selMunicipio.value;
    if (!municipio) {
      maximoLitros = null;
      inputVolumen.removeAttribute("placeholder");
      inputVolumen.removeAttribute("max");
      mensajeVolumenDiv.innerHTML = "";
      return;
    }
    const esFrontera = ubicaciones[selDepartamento.value][selProvincia.value][municipio].es_frontera;
    maximoLitros = esFrontera ? LITROS_MAXIMO_FRONTERA : LITROS_MAXIMO_NO_FRONTERA;
    inputVolumen.placeholder = `Máximo ${maximoLitros} litros`;
    inputVolumen.max = String(maximoLitros);
    validarVolumen();
  };

  const repoblarMunicipios = () => {
    const departamento = selDepartamento.value;
    const provincia = selProvincia.value;
    if (!departamento || !provincia) {
      llenarSelect(selMunicipio, [], { placeholder: "Elegir..." });
      actualizarLimiteVolumen();
      return;
    }
    llenarSelect(selMunicipio, Object.keys(ubicaciones[departamento][provincia]), { placeholder: "Elegir..." });
    actualizarLimiteVolumen();
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

  if (estado.campos) {
    // Reconstrucción vía "volver": precarga con lo ya ingresado. Fijar el
    // `.value` del select padre ANTES de repoblar el hijo — cada
    // `repoblarX` lee `.value` del padre ya fijado.
    const c = estado.campos;
    selDepartamento.value = c.departamento;
    repoblarProvincias();
    selProvincia.value = c.provincia;
    repoblarMunicipios();
    selMunicipio.value = c.municipio;
    actualizarLimiteVolumen();
    nodo.querySelector("#input-direccion").value = c.direccion;
    nodo.querySelector("#sel-actividad").value = c.actividad;
    nodo.querySelector("#sel-producto").value = c.producto;
    inputVolumen.value = c.volumen_litros;
    nodo.querySelector("#input-uso").value = c.uso_destino;
    validarVolumen();
  } else {
    repoblarProvincias();
  }

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

    validarVolumen();
    if (maximoLitros != null && volumenLitros > maximoLitros) {
      return;
    }

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
    limpiarDesdeFoto();
    congelar(nodo);
    irAPaso3();
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
      <button id="boton-continuar-paso3" class="boton-primario boton-ancho-completo" disabled>Continuar</button>
      <div id="mensaje-paso3"></div>
    </div>
  `;
  const nodo = panel.firstElementChild;
  const filaFormulario = crearBurbujaFormulario(nodo);
  contenedorMensajes.appendChild(filaFormulario);
  pasoActivo.nodoFormulario = filaFormulario;
  irAlFinal();

  const inputFoto = nodo.querySelector("#input-foto");
  const botonAdjuntar = nodo.querySelector("#boton-adjuntar-foto");
  const botonQuitar = nodo.querySelector("#boton-quitar-foto");
  const confirmacion = nodo.querySelector("#confirmacion-foto");
  const iconoArchivo = nodo.querySelector(".icono-archivo");
  const boton = nodo.querySelector("#boton-continuar-paso3");

  let urlPreviaFoto = null;

  // Reconstrucción vía "volver": un <input type="file"> no se puede
  // prellenar por seguridad del navegador, así que se muestra el preview
  // desde el base64 ya guardado en `estado` y se habilita "Continuar"
  // directamente (la foto ya fue validada contra el servicio antes).
  if (estado.fotoBase64) {
    iconoArchivo.innerHTML = `<img src="data:${estado.fotoMime};base64,${estado.fotoBase64}" alt="" />`;
    confirmacion.classList.remove("oculto");
    botonQuitar.classList.remove("oculto");
    confirmacion.querySelector(".nombre-archivo").textContent = estado.fotoNombre;
    confirmacion.querySelector(".tamano-archivo").innerHTML = "✓ Foto ya cargada";
    boton.disabled = false;
  }

  botonAdjuntar.addEventListener("click", () => inputFoto.click());

  botonQuitar.addEventListener("click", () => {
    inputFoto.value = "";
    if (urlPreviaFoto) {
      URL.revokeObjectURL(urlPreviaFoto);
      urlPreviaFoto = null;
    }
    estado.fotoBase64 = null;
    estado.fotoNombre = null;
    estado.fotoMime = null;
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

  const mensajeDiv = nodo.querySelector("#mensaje-paso3");

  boton.addEventListener("click", async () => {
    const archivo = inputFoto.files[0];
    if (!archivo && !estado.fotoBase64) return;
    mensajeDiv.innerHTML = "";
    boton.disabled = true;

    let fotoBase64, fotoMime, fotoNombre;

    if (archivo) {
      const dataUrl = await leerComoDataUrl(archivo);
      fotoBase64 = dataUrl.split(",")[1];
      fotoMime = archivo.type || "image/jpeg";
      fotoNombre = archivo.name;

      mensajeDiv.innerHTML = `<p class="texto-aviso">Validando fotografía...</p>`;
      try {
        const resultado = await validarImagenTitular(fotoBase64, fotoMime, fotoNombre);
        if (resultado.veredicto !== "VALIDA") {
          mensajeDiv.innerHTML = `<p class="texto-aviso">${resultado.motivo}</p>`;
          boton.disabled = false;
          return;
        }
      } catch (error) {
        const mensaje = error instanceof ApiError ? error.mensaje : "Ocurrió un error inesperado.";
        mensajeDiv.innerHTML = `<p class="texto-error">${mensaje}</p>`;
        boton.disabled = false;
        return;
      }
      mensajeDiv.innerHTML = "";
    } else {
      // No se eligió un archivo nuevo en esta pasada (reconstrucción vía
      // "volver"): reusar la foto ya validada antes, sin volver a llamar al
      // servicio de validación de imágenes.
      fotoBase64 = estado.fotoBase64;
      fotoMime = estado.fotoMime;
      fotoNombre = estado.fotoNombre;
    }

    estado.fotoBase64 = fotoBase64;
    estado.fotoNombre = fotoNombre;
    estado.fotoMime = fotoMime;
    limpiarDesdeEnvio();
    congelar(nodo);
    irAPaso4();
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
      <button id="boton-enviar" class="boton-primario boton-ancho-completo" disabled>Confirmar y enviar</button>
      <div id="mensaje-paso4"></div>
    </div>
  `;
  const nodo = panel.firstElementChild;
  const filaFormulario = crearBurbujaFormulario(nodo);
  contenedorMensajes.appendChild(filaFormulario);
  pasoActivo.nodoFormulario = filaFormulario;
  irAlFinal();

  const checkbox = nodo.querySelector("#input-jurada");
  const boton = nodo.querySelector("#boton-enviar");
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
      // Paso 5 es terminal: no hay forma de volver, así que se le quita el
      // botón "volver" a la burbuja de Paso 4 (mismo criterio que
      // `avanzarAPaso`) y el paso se archiva en el historial (higiene);
      // `pasoActivo` queda en `null` reflejando que el wizard terminó.
      pasoActivo.nodoIntro.querySelector(".boton-volver-paso")?.remove();
      historialPasos.push(pasoActivo);
      pasoActivo = null;
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

  contenedorMensajes.appendChild(crearBurbujaPaso(5, "RESULTADO", texto));
  irAlFinal();
}
