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

El chat actúa como proxy de las tres APIs. Los usuarios solo necesitan acceder
al puerto del chat; no se publican los puertos internos de Backend, Ciudadania
Digital ni RAG en el navegador.

Para una prueba local aislada, usar puertos alternativos:

```bash
BACKEND_HOST_PORT=18001 \
CIUDADANIA_HOST_PORT=18002 \
RAG_HOST_PORT=18003 \
CHAT_HOST_PORT=18080 \
docker compose -f scripts/cloud/compose.test.yml up -d
```

Abrir `http://127.0.0.1:18080`.

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

Para una sesión remota de costo cero, iniciar un Quick Tunnel sobre el puerto
del chat. La URL HTTPS generada será la única que se comparte con el equipo:

```bash
cloudflared tunnel --url http://127.0.0.1:18080
```

Cerrar el proceso `cloudflared` al terminar la ventana de prueba. El Quick
Tunnel es temporal y está destinado a pruebas, no a producción.

## Smoke test

Con el tunel activo, desde la raiz del repositorio:

```bash
python scripts/cloud/smoke_test.py
```

La prueba usa solamente datos sinteticos y escribe
`docs/evidencias/prueba_cloud_20260924.json`.
