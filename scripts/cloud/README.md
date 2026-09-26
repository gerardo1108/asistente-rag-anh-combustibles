# Scripts de prueba temporal en nube

Herramientas auxiliares para repetir una prueba tecnica por SSH con datos
sinteticos. No publican la aplicacion en Internet ni reemplazan el despliegue
HTTPS con control de acceso descrito en `docs/despliegue_pruebas_equipo.md`.

## Compose de prueba

Desde `asistente-anh/`:

```bash
docker compose -f ../scripts/cloud/compose.test.yml up -d --build
```

Los servicios quedan expuestos solo en `127.0.0.1` dentro de la VM:

- chat: `8080`
- Backend ANH: `8001`
- Ciudadania Digital: `8002`
- RAG: `8003`

El chat se configura para que el navegador use los puertos locales del tunel
SSH: `18001`, `18002` y `18003`.

## Tunel SSH

Desde la maquina local:

```bash
ANH_GCP_INSTANCE=nombre-vm \
ANH_GCP_PROJECT=id-proyecto \
ANH_GCP_ZONE=us-central1-a \
sh scripts/cloud/tunnel.sh
```

Mantener esa terminal abierta durante la prueba. Luego abrir:

- `http://127.0.0.1:18080`
- `http://127.0.0.1:18080/supervisor`

## Smoke test

Con el tunel activo, desde la raiz del repositorio:

```bash
python scripts/cloud/smoke_test.py
```

La prueba usa solamente datos sinteticos y escribe
`docs/evidencias/prueba_cloud_20260924.json`.
