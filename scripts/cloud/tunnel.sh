#!/bin/sh
# Mantener esta terminal abierta durante la prueba. Ctrl+C cierra el túnel.
set -eu

: "${ANH_GCP_INSTANCE:?Definir ANH_GCP_INSTANCE con el nombre de la VM}"
: "${ANH_GCP_PROJECT:?Definir ANH_GCP_PROJECT con el ID del proyecto}"
: "${ANH_GCP_ZONE:=us-central1-a}"

exec gcloud compute ssh "$ANH_GCP_INSTANCE" \
  --project="$ANH_GCP_PROJECT" --zone="$ANH_GCP_ZONE" --quiet -- \
  -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 127.0.0.1:18080:127.0.0.1:8080 \
  -L 127.0.0.1:18001:127.0.0.1:8001 \
  -L 127.0.0.1:18002:127.0.0.1:8002 \
  -L 127.0.0.1:18003:127.0.0.1:8003
