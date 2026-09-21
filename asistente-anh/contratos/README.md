# Contratos

Especificaciones OpenAPI 3.0.3. **Fuente de verdad**: si una implementación no
coincide con la spec, se corrige la implementación.

| Archivo | Servicio | Puerto |
|---|---|---|
| `openapi-integracion.yaml` | Backend ANH — contrato estándar | 8001 |
| `openapi-supervision-anh.yaml` | Backend ANH — operaciones internas | 8001 |
| `openapi-ciudadania-digital.yaml` | Ciudadanía Digital | 8002 |
| `openapi-utilidades-prototipo.yaml` | Ambos servicios | 8001 y 8002 |

Las dos primeras las implementa el mismo servicio, sobre los mismos datos. La
separación es documental: distingue el contrato estándar, que cualquier entidad
podría adoptar, de las operaciones particulares de la ANH.

Las utilidades (`/health` y `/reiniciar`) son instrumentación del prototipo, no
del dominio del trámite. Ambos servicios las exponen. El reinicio recarga las
semillas y solo responde si la variable `PERMITIR_REINICIO` está activa.

Para verlas renderizadas: pegar el contenido en https://editor.swagger.io, o
usar la extensión *OpenAPI (Swagger) Editor* en VS Code.

**Cualquier cambio a estos archivos afecta al orquestador y al panel del
evaluador. Comunicarlo al equipo.**
