# RAG para CPU: optimización y medición local

## Alcance

Trabajo en `optimizacion/rag-cpu`, posterior a `v0.2.0`. No se modificó esa
etiqueta ni se crearon recursos en Google Cloud. El servicio habitual de la
V2 conserva su imagen; las mediciones usan contenedores temporales separados.

## Cambios

- PyTorch `2.14.0+cpu` instalado desde el índice oficial CPU antes de instalar
  el resto de requisitos. La construcción comprueba `torch.version.cuda is None`.
- Verificación de la imagen: sin paquetes `nvidia-*` ni `cuda-*`.
- El Dockerfile copia únicamente `src/rag`, evitando incluir otros servicios.
- Modelo de embeddings e índice construidos en la imagen. Se activa el modo
  offline de Hugging Face al ejecutarla, evitando consultas de descarga al
  arrancar. Las llamadas de generación a Groq siguen requiriendo Internet.

Referencia: [instalación oficial de PyTorch](https://docs.pytorch.org/get-started/locally/).

## Método

Docker Desktop sobre Apple Silicon, imágenes Linux ARM64. Tres contenedores
nuevos por imagen, ejecutados secuencialmente con **1 CPU y 2 GiB de RAM**.
Ambas imágenes usan los mismos proveedores y modo offline de embeddings.
La máquina mantiene otros servicios activos; no es un banco de pruebas aislado.

Tiempo de arranque: desde iniciar `docker run` hasta que `/docs` devuelve 200.
No incluye descargar la imagen. No se vació la caché de disco del anfitrión;
son arranques de contenedores nuevos, no arranques en máquinas completamente frías.
Cada ronda realiza una consulta normativa real a Groq y exige fuentes.

RSS corresponde al proceso del servidor; los contadores cgroup incluyen memoria
atribuida al contenedor y cachés. Su contabilidad no coincide necesariamente con
RSS. Las lecturas cgroup también incluyen el pequeño proceso de medición.
No se midió concurrencia, carga sostenida ni escalado.

## Resultados

| Métrica | Imagen anterior | Imagen CPU |
|---|---:|---:|
| Tamaño local reportado por Docker, GB decimales | 3,936 | 0,937 |
| Mediana de arranque | 7,376 s | 7,098 s |
| Mediana RSS tras consulta | 1551 MiB | 1204 MiB |
| Mayor pico cgroup observado | 1261 MiB | 1299 MiB |
| Mediana de consulta HTTP, incluido Groq | 0,931 s | 0,920 s |
| Consultas con fuentes presentes y Groq confirmado | 3/3 | 3/3 |

Reducción de tamaño de aproximadamente **76,2 %** y de RSS tras consulta de
aproximadamente **22,4 %**. El pico cgroup no bajó: no se concluye que el
límite de memoria pueda reducirse en esa misma proporción. La diferencia de
latencia y arranque es pequeña y no constituye evidencia de mejora sostenida.
El tamaño local no equivale al tamaño comprimido ni al costo de Artifact Registry.

Datos completos: [medición de recursos](evidencias/recursos_rag_cpu.json).

## Regresión funcional y límite observado

Se ejecutaron además las seis consultas de `eval/validar_rag.py` contra la
imagen CPU. Pasaron las cinco comprobaciones automáticas de campos, fuentes
y abstención; la pregunta de volumen no documentado también produjo abstención.
[Respuestas completas](evidencias/evaluacion_rag_cpu.json).

La revisión humana de la pregunta con contexto encontró ejemplos de fotografías
y destinos no enumerados en el corpus. El modelo sigue pudiendo introducir
ese detalle pese al refuerzo del prompt. Este ensayo no establece que lo cause
el cambio de PyTorch: se observó ese comportamiento antes de la optimización y
la generación no es determinista. No se declara resuelta la fidelidad total al
corpus ni se considera suficiente comprobar solo `encontrado` y `fuentes`.
Es un pendiente de calidad independiente para revisar antes de una exposición pública.

## Reproducir

Desde `asistente-anh/`, conservar primero la referencia de la imagen anterior:

```bash
docker tag asistente-anh-rag anh-rag:baseline-v020
docker build -t anh-rag:cpu -f src/rag/Dockerfile .
python eval/medir_recursos.py --images anh-rag:baseline-v020 anh-rag:cpu \
  --report ../docs/evidencias/recursos_rag_cpu.json
```

El script usa `.env` sin imprimir secretos, publica puertos aleatorios solo en
localhost y elimina únicamente sus propios contenedores temporales al terminar.
Realiza una llamada al proveedor por ronda y consume cuota. En este Mac puede
pasarse `--docker /Applications/Docker.app/Contents/Resources/bin/docker`.

## Dimensionamiento inicial

**1 CPU y 2 GiB para el servicio RAG** son un punto de partida probado localmente,
no una garantía de capacidad en Cloud Run. No elegir 1 GiB: el pico observado
supera ese límite. Falta medir concurrencia antes de fijar solicitudes por instancia.

Estas mediciones ARM64 no sustituyen construir y probar la imagen para la
arquitectura y plataforma elegidas en Google Cloud. Tampoco constituyen una
estimación de factura. El siguiente paso de planificación es resolver la
persistencia y adaptar los endpoints HTTPS antes de proponer el despliegue.
