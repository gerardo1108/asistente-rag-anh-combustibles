import { ApiError, obtenerSolicitud, resolverSolicitud } from "./api-client.js";

const ETIQUETAS_ESTADO = {
  REGISTRADO: "Registrado",
  APROBADO: "Aprobado",
  RECHAZADO: "Rechazado",
};

function codigoDesdeUrl() {
  const partes = window.location.pathname.split("/").filter(Boolean);
  return decodeURIComponent(partes[partes.length - 1]);
}

function valorDe(datos, campo) {
  return datos.find((d) => d.campo === campo)?.valor ?? "—";
}

function formatearFecha(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-BO", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function cargar() {
  const codigo = codigoDesdeUrl();
  const contenedor = document.getElementById("contenido-detalle");

  try {
    const solicitud = await obtenerSolicitud(codigo);
    render(contenedor, codigo, solicitud);
  } catch (error) {
    if (error instanceof ApiError && error.statusCode === 404) {
      contenedor.innerHTML = '<div class="tarjeta"><p class="texto-error">No encontramos esa solicitud.</p></div>';
    } else {
      const mensaje = error instanceof ApiError ? error.mensaje : "Ocurrió un error inesperado.";
      contenedor.innerHTML = `<div class="tarjeta"><p class="texto-error">${mensaje}</p></div>`;
    }
  }
}

function render(contenedor, codigo, solicitud) {
  const t = solicitud.solicitante;
  const datos = solicitud.datos;
  const foto = solicitud.adjuntos.find((a) => a.tipo === "FOTO_TITULAR_CON_CI");

  const nombreCompleto = [t.nombres, t.primer_apellido, t.segundo_apellido].filter(Boolean).join(" ");

  contenedor.innerHTML = `
    <div class="tarjeta">
      <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom: 12px;">
        <h2 style="margin:0;">${solicitud.codigo_tramite}</h2>
        <span class="badge badge-${solicitud.estado.toLowerCase()}">${ETIQUETAS_ESTADO[solicitud.estado] ?? solicitud.estado}</span>
      </div>
      <p style="color: var(--sup-texto-secundario); font-size: 13px; margin: 0 0 16px 0;">
        Registrado el ${formatearFecha(solicitud.fecha_registro)}
        ${solicitud.fecha_resolucion ? ` — resuelto el ${formatearFecha(solicitud.fecha_resolucion)}` : ""}
      </p>

      <div class="detalle-grid">
        <div class="detalle-foto">
          ${
            foto
              ? `<img src="data:${foto.mime};base64,${foto.contenido_base64}" alt="Foto de verificación de identidad" />`
              : '<p class="texto-error">Sin foto de verificación adjunta.</p>'
          }
        </div>

        <div>
          <div class="detalle-seccion">
            <h3>Datos del solicitante</h3>
            <p><strong>Nombre:</strong> ${nombreCompleto}</p>
            <p><strong>Documento:</strong> ${t.tipo_documento} ${t.numero_documento}</p>
          </div>

          <div class="detalle-seccion">
            <h3>Ubicación de la compra</h3>
            <p><strong>Departamento:</strong> ${valorDe(datos, "departamento")}</p>
            <p><strong>Provincia:</strong> ${valorDe(datos, "provincia")}</p>
            <p><strong>Municipio:</strong> ${valorDe(datos, "municipio")}</p>
            <p><strong>Dirección:</strong> ${valorDe(datos, "direccion")}</p>
          </div>

          <div class="detalle-seccion">
            <h3>Detalle del combustible</h3>
            <p><strong>Actividad:</strong> ${valorDe(datos, "actividad")}</p>
            <p><strong>Producto:</strong> ${valorDe(datos, "producto")}</p>
            <p><strong>Volumen declarado:</strong> ${valorDe(datos, "volumen_litros")} litros</p>
          </div>

          <div class="detalle-seccion">
            <h3>Justificación</h3>
            <p>${valorDe(datos, "uso_destino")}</p>
          </div>

          ${solicitud.estado === "RECHAZADO" && solicitud.motivo_rechazo
            ? `<div class="detalle-seccion"><h3>Motivo del rechazo</h3><p class="texto-error">${solicitud.motivo_rechazo}</p></div>`
            : ""}
        </div>
      </div>

      <div id="panel-acciones" style="margin-top: 20px;"></div>
    </div>
  `;

  if (solicitud.estado === "REGISTRADO") {
    renderAcciones(codigo);
  }
}

function renderAcciones(codigo) {
  const panel = document.getElementById("panel-acciones");
  panel.innerHTML = `
    <div class="panel-acciones" id="panel-botones">
      <button type="button" class="boton-primario" id="boton-aprobar">Aprobar</button>
      <button type="button" class="boton-secundario boton-rechazar" id="boton-rechazar">Rechazar</button>
    </div>
    <div class="panel-rechazo" id="panel-rechazo" style="display:none; margin-top: 12px;">
      <textarea id="input-motivo" placeholder="Motivo del rechazo (obligatorio)"></textarea>
      <div id="mensaje-rechazo"></div>
      <div style="display:flex; gap:10px;">
        <button type="button" class="boton-primario boton-rechazar" id="boton-confirmar-rechazo">Confirmar rechazo</button>
        <button type="button" class="boton-secundario" id="boton-cancelar-rechazo">Cancelar</button>
      </div>
    </div>
    <div id="mensaje-accion"></div>
  `;

  document.getElementById("boton-aprobar").addEventListener("click", async () => {
    await ejecutarResolucion(codigo, "APROBADO");
  });

  document.getElementById("boton-rechazar").addEventListener("click", () => {
    document.getElementById("panel-botones").style.display = "none";
    document.getElementById("panel-rechazo").style.display = "block";
  });

  document.getElementById("boton-cancelar-rechazo").addEventListener("click", () => {
    document.getElementById("panel-rechazo").style.display = "none";
    document.getElementById("panel-botones").style.display = "flex";
  });

  document.getElementById("boton-confirmar-rechazo").addEventListener("click", async () => {
    const motivo = document.getElementById("input-motivo").value.trim();
    const mensajeDiv = document.getElementById("mensaje-rechazo");
    if (!motivo) {
      mensajeDiv.innerHTML = '<p class="texto-error">El motivo es obligatorio.</p>';
      return;
    }
    await ejecutarResolucion(codigo, "RECHAZADO", motivo);
  });
}

async function ejecutarResolucion(codigo, estado, motivo) {
  const mensajeDiv = document.getElementById("mensaje-accion") ?? document.getElementById("mensaje-rechazo");
  try {
    await resolverSolicitud(codigo, estado, motivo);
    await cargar();
  } catch (error) {
    const mensaje = error instanceof ApiError ? error.mensaje : "Ocurrió un error inesperado.";
    mensajeDiv.innerHTML = `<p class="texto-error">${mensaje}</p>`;
  }
}

document.addEventListener("DOMContentLoaded", cargar);
