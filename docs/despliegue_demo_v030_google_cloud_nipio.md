# Despliegue de demo en Google Cloud con nip.io

Guía operativa para repetir el despliegue temporal de la demo desde la etiqueta
`v0.3.0`. La configuración está destinada únicamente a pruebas académicas con
datos sintéticos.

## Alcance y advertencias

- Proyecto: `asistente-anh-demo-3011h`.
- Región/zona: `us-central1-a`.
- Máquina: `e2-medium`, disco estándar de 30 GiB.
- La VM es temporal y debe eliminarse al terminar la ventana de pruebas.
- Se configuró apagado automático de cuatro horas como protección operativa.
- ANH, Ciudadanía Digital y la validación institucional son simulaciones.
- No usar CI, fotografías, correos ni solicitudes reales.
- La publicación abierta sin credenciales solo debe usarse durante una ventana
  controlada. El panel `/supervisor` queda accesible desde su enlace.
- `nip.io` ofrece resolución basada en la IP pública, pero no es un dominio
  institucional ni una configuración de producción.

## Referencia de código

La demo desplegada se construye desde:

```text
Etiqueta: v0.3.0
Commit: 792f4a3
Repositorio: gerardo1108/asistente-rag-anh-combustibles
```

La etiqueta no contiene por sí sola el Compose completo de publicación. Para
el despliegue se agrega una capa temporal que incorpora:

- Dockerfile del servicio web `chat`.
- Compose con cinco servicios internos y Caddy.
- Caddy como único punto público en 80/443.
- Rutas `/api/backend-anh`, `/api/ciudadania-digital`, `/api/rag` y
  `/api/validacion-imagenes`.
- `PERMITIR_REINICIO=false`.
- PyTorch CPU para evitar descargar paquetes CUDA en la VM sin GPU.

## Preparación local

Comprobar autenticación y proyecto:

```bash
gcloud auth list
gcloud config set project asistente-anh-demo-3011h
```

Preparar una copia temporal de la etiqueta, sin modificar `main`:

```bash
DEPLOY_DIR=$(mktemp -d /tmp/anh-v030-deploy.XXXXXX)
git archive v0.3.0 | tar -x -C "$DEPLOY_DIR"
```

Copiar las variables privadas a `"$DEPLOY_DIR/.env"`. Como mínimo se necesita
`GOOGLE_API_KEY`; definir explícitamente:

```env
LLM_PROVEEDORES=gemini
VALIDACION_IMAGENES_PROVEEDORES=gemini
```

El archivo `.env` debe permanecer fuera de GitHub y con permisos restrictivos:

```bash
chmod 600 "$DEPLOY_DIR/.env"
```

## Red y VM

Crear una regla que permita solo HTTP y HTTPS al tag de la VM:

```bash
gcloud compute firewall-rules create anh-piloto-http \
  --network=default \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:80,tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=anh-piloto-web
```

Crear la VM:

```bash
gcloud compute instances create asistente-anh-piloto \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --tags=anh-piloto-web \
  --metadata='serial-port-enable=0,startup-script=#!/bin/bash
set -eux
apt-get update
apt-get install -y docker.io docker-compose-v2
systemctl enable --now docker
mkdir -p /opt/asistente-anh
shutdown -h +240'
```

Si el `apt-get` de inicio queda ejecutándose, esperar a que termine antes de
instalar Docker manualmente. Verificar:

```bash
gcloud compute ssh asistente-anh-piloto --zone=us-central1-a \
  --command='docker --version && docker compose version'
```

## Dominio nip.io y Caddy

Obtener la IP pública:

```bash
gcloud compute instances describe asistente-anh-piloto \
  --zone=us-central1-a \
  --format='value(networkInterfaces[0].accessConfigs[0].natIP)'
```

Convertir la IP, por ejemplo `35.184.37.29`, a:

```text
35-184-37-29.nip.io
```

Caddy debe recibir ese host y publicar únicamente:

```text
https://35-184-37-29.nip.io/
https://35-184-37-29.nip.io/supervisor
```

El Caddyfile debe enviar las rutas `/api/*` a los servicios internos y el resto
al servicio `chat`. No se deben publicar directamente los puertos 8001, 8002,
8003, 8004 ni 8080.

## Copia y arranque

Crear previamente `/tmp/anh-v030-upload` en la VM y copiar la capa de despliegue
y la copia privada de `.env`:

```bash
gcloud compute ssh asistente-anh-piloto --zone=us-central1-a \
  --command='mkdir -p /tmp/anh-v030-upload'

gcloud compute scp --recurse "$DEPLOY_DIR/." \
  asistente-anh-piloto:/tmp/anh-v030-upload/ \
  --zone=us-central1-a

gcloud compute ssh asistente-anh-piloto --zone=us-central1-a \
  --command='sudo cp -a /tmp/anh-v030-upload/. /opt/asistente-anh/'
```

Levantar el despliegue:

```bash
gcloud compute ssh asistente-anh-piloto --zone=us-central1-a \
  --command='cd /opt/asistente-anh && sudo docker compose -f docker-compose.deploy.yml up -d --build'
```

El primer build del RAG puede tardar varios minutos porque descarga el modelo
de embeddings. El Dockerfile de publicación debe instalar `torch` desde el
índice CPU de PyTorch; no usar el paquete general en esta VM.

## Verificación mínima

Desde otra red, comprobar:

```bash
curl -I https://35-184-37-29.nip.io/
curl -I https://35-184-37-29.nip.io/supervisor
```

Ambos deben devolver `200`. Verificar en la VM:

```bash
cd /opt/asistente-anh
sudo docker compose -f docker-compose.deploy.yml ps
sudo ss -ltn
```

Solo Caddy debe escuchar públicamente en 80/443. Ejecutar después el flujo
manual de consulta, registro, carga de imagen sintética, seguimiento y
supervisión usando los datos de `semillas/`.

## Persistencia y datos

La demo utiliza volúmenes Docker para SQLite. Antes de eliminar la VM, detener
los escritores y respaldar las bases si se necesita conservar evidencia. No
subir bases, fotografías, logs ni `.env` al repositorio.

## Cierre y control de costos

Al terminar:

```bash
gcloud compute ssh asistente-anh-piloto --zone=us-central1-a \
  --command='cd /opt/asistente-anh && sudo docker compose -f docker-compose.deploy.yml down'

gcloud compute instances delete asistente-anh-piloto \
  --zone=us-central1-a
```

Eliminar también la regla creada para la demo si ya no se reutilizará:

```bash
gcloud compute firewall-rules delete anh-piloto-http
```

Confirmar que no queden VM, discos independientes, IP reservadas ni repositorios
de Artifact Registry:

```bash
gcloud compute instances list
gcloud compute disks list
gcloud compute addresses list
gcloud artifacts repositories list --location=us-central1
```

Apagar Docker o detener contenedores no elimina el costo de la VM. La forma
confiable de cerrar la sesión es eliminar los recursos temporales y revisar la
facturación del proyecto.
