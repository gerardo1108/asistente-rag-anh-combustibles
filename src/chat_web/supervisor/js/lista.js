import { ApiError, listarSolicitudes } from "./api-client.js";
import { POR_PAGINA } from "./config.js";

const ETIQUETAS_ESTADO = {
  REGISTRADO: "Registrado",
  APROBADO: "Aprobado",
  RECHAZADO: "Rechazado",
};

let estadoFiltro = "";
let paginaActual = 1;
let textoBusqueda = "";
let idTimeoutBusqueda = null;

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".filtro-estado").forEach((boton) => {
    boton.addEventListener("click", () => {
      estadoFiltro = boton.dataset.estado;
      paginaActual = 1;
      document.querySelectorAll(".filtro-estado").forEach((b) => b.classList.toggle("activo", b === boton));
      cargar();
    });
  });
  document.querySelector('.filtro-estado[data-estado=""]').classList.add("activo");

  document.getElementById("input-buscar").addEventListener("input", (evento) => {
    clearTimeout(idTimeoutBusqueda);
    idTimeoutBusqueda = setTimeout(() => {
      textoBusqueda = evento.target.value.trim();
      paginaActual = 1;
      cargar();
    }, 300);
  });

  cargar();
});

function formatearFecha(iso) {
  return new Date(iso).toLocaleDateString("es-BO", { year: "numeric", month: "2-digit", day: "2-digit" });
}

function crearFila(solicitud) {
  const fila = document.createElement("div");
  fila.className = "fila-solicitud";

  const celdas = [
    ["Código", solicitud.codigo_tramite],
    ["Fecha", formatearFecha(solicitud.fecha_registro)],
    ["Solicitante", solicitud.solicitante],
    ["Tipo doc.", "CI"],
    ["N.º documento", solicitud.numero_documento],
    ["Estado", null],
    ["", null],
  ];

  for (const [etiqueta, valor] of celdas) {
    const celda = document.createElement("div");
    if (etiqueta) {
      const spanEtiqueta = document.createElement("span");
      spanEtiqueta.className = "celda-etiqueta";
      spanEtiqueta.textContent = etiqueta;
      celda.appendChild(spanEtiqueta);
    }
    if (valor !== null) {
      celda.appendChild(document.createTextNode(valor));
    }
    fila.appendChild(celda);
  }

  const celdaEstado = fila.children[5];
  const badge = document.createElement("span");
  badge.className = `badge badge-${solicitud.estado.toLowerCase()}`;
  badge.textContent = ETIQUETAS_ESTADO[solicitud.estado] ?? solicitud.estado;
  celdaEstado.appendChild(badge);

  const celdaAccion = fila.children[6];
  const boton = document.createElement("a");
  boton.className = "boton-secundario";
  boton.href = `/supervisor/solicitud/${encodeURIComponent(solicitud.codigo_tramite)}`;
  boton.textContent = "Ver detalle";
  boton.style.textDecoration = "none";
  boton.style.display = "inline-block";
  celdaAccion.appendChild(boton);

  return fila;
}

async function cargar() {
  const contenedor = document.getElementById("lista-solicitudes");
  const paginacion = document.getElementById("paginacion");
  contenedor.innerHTML = "";
  paginacion.innerHTML = "";

  try {
    const resultado = await listarSolicitudes({
      estado: estadoFiltro || undefined,
      pagina: paginaActual,
      porPagina: POR_PAGINA,
      q: textoBusqueda || undefined,
    });

    if (resultado.solicitudes.length === 0) {
      contenedor.innerHTML = '<p class="texto-vacio">No hay solicitudes que coincidan con la búsqueda.</p>';
      return;
    }

    const encabezado = document.createElement("div");
    encabezado.className = "fila-solicitud encabezado";
    ["Código", "Fecha", "Solicitante", "Tipo doc.", "N.º documento", "Estado", ""].forEach((texto) => {
      const celda = document.createElement("div");
      celda.textContent = texto;
      encabezado.appendChild(celda);
    });
    contenedor.appendChild(encabezado);

    for (const solicitud of resultado.solicitudes) {
      contenedor.appendChild(crearFila(solicitud));
    }

    const totalPaginas = Math.max(1, Math.ceil(resultado.total / POR_PAGINA));
    if (totalPaginas > 1) {
      const botonAnterior = document.createElement("button");
      botonAnterior.className = "boton-secundario";
      botonAnterior.textContent = "Anterior";
      botonAnterior.disabled = paginaActual <= 1;
      botonAnterior.addEventListener("click", () => {
        paginaActual -= 1;
        cargar();
      });

      const indicador = document.createElement("span");
      indicador.textContent = `Página ${paginaActual} de ${totalPaginas}`;

      const botonSiguiente = document.createElement("button");
      botonSiguiente.className = "boton-secundario";
      botonSiguiente.textContent = "Siguiente";
      botonSiguiente.disabled = paginaActual >= totalPaginas;
      botonSiguiente.addEventListener("click", () => {
        paginaActual += 1;
        cargar();
      });

      paginacion.append(botonAnterior, indicador, botonSiguiente);
    }
  } catch (error) {
    const mensaje = error instanceof ApiError ? error.mensaje : "Ocurrió un error inesperado.";
    contenedor.innerHTML = `<p class="texto-error">${mensaje}</p>`;
  }
}
