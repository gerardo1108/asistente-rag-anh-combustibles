# Despliegue planeado en Google Cloud Run

## Objetivo

Este documento deja preparado el camino para publicar el prototipo en Google
Cloud Run durante la presentacion o grabacion del video, sin ejecutar todavia el
despliegue.

La meta es que el equipo pueda mostrar una URL publica temporal del asistente
sin depender de un equipo local encendido.

## Estado Actual

El proyecto ya queda preparado para contenedor:

- `Dockerfile`: construye una imagen Python minima.
- `.dockerignore`: excluye archivos locales, cache, datos de demo y documentos
  internos.
- `src/app.py`: acepta `APP_PORT` para local y `PORT` para Cloud Run.
- El MVP no requiere dependencias externas ni claves de API.

## Recomendacion de Servicio

Para la demo se recomienda Google Cloud Run porque:

- Ejecuta aplicaciones HTTP en contenedores.
- Puede escalar a cero cuando no hay trafico.
- Permite limitar instancias para controlar costos.
- No requiere mantener una maquina virtual encendida.

## Consideraciones de Costo

Cloud Run cuenta con capa gratuita mensual, pero no debe describirse como costo
cero garantizado. La recomendacion para mantener el consumo controlado es:

- Usar `min-instances=0`.
- Usar `max-instances=1`.
- Usar memoria baja, por ejemplo `256Mi`.
- Evitar bases de datos administradas en esta fase.
- Evitar llamadas a APIs externas pagadas.
- Configurar alertas de presupuesto en Google Cloud Billing.
- Apagar o eliminar el servicio despues de la presentacion si ya no se usa.

## Limitacion de Persistencia

Cloud Run usa contenedores efimeros. El archivo local
`data/solicitudes_demo.json` puede perderse cuando la instancia se reinicia o
escala a cero. Para la demo esto es aceptable, pero no debe presentarse como
persistencia productiva.

Si se necesita persistencia real en una fase posterior, se recomienda evaluar:

- Firestore.
- Cloud SQL.
- Cloud Storage para archivos simples.

## Prueba Local con Docker

Desde la raiz del repositorio:

```bash
docker build -t asistente-rag-anh .
docker run --rm -p 8080:8080 asistente-rag-anh
```

Luego abrir:

```text
http://127.0.0.1:8080
```

Nota: para ejecutar estos comandos, Docker Desktop o el daemon de Docker debe
estar activo en el equipo.

## Comandos de Despliegue Planeado

Estos comandos son una guia para cuando el equipo decida desplegar. No se han
ejecutado en esta fase.

1. Autenticarse:

```bash
gcloud auth login
gcloud config set project ID_DEL_PROYECTO
```

2. Habilitar APIs necesarias:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

3. Desplegar desde el codigo fuente:

```bash
gcloud run deploy asistente-rag-anh \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 1 \
  --memory 256Mi \
  --set-env-vars RAG_MODE=hybrid,APP_HOST=0.0.0.0
```

4. Ver estado del servicio:

```bash
gcloud run services describe asistente-rag-anh \
  --region us-central1
```

5. Eliminar el servicio despues de la demo, si aplica:

```bash
gcloud run services delete asistente-rag-anh \
  --region us-central1
```

## Criterios para Usarlo en la Presentacion

Antes de grabar el video o exponer el prototipo:

1. Ejecutar pruebas locales:

```bash
python3 eval/evaluate_rag.py --mode both
python3 -m unittest discover -s tests
```

2. Probar localmente la interfaz:

```text
http://127.0.0.1:8001
```

3. Si se despliega, validar la URL publica generada por Cloud Run.

4. Mostrar durante la demo:

- Consulta normativa con fuentes.
- Registro guiado exitoso.
- Rechazo por volumen excedido.
- Panel evaluador simulado.
- Documento `docs/validacion_prototipo.md` como evidencia tecnica.
