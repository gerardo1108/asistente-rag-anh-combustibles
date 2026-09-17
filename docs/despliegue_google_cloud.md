# Guia de despliegue temporal en Google Cloud Run

## Estado del documento

Propuesta tecnica para revision del equipo. No representa una decision final.
La rama `integracion/servicios-externos` permanece separada hasta acordar la
arquitectura con el equipo.

## Objetivo

Publicar temporalmente el MVP para pruebas coordinadas, conservando la
separacion entre el asistente, Backend ANH y Ciudadania Digital. El despliegue
debe servir para validacion academica y no se considera un entorno productivo.

## Antecedentes

El prototipo monolitico se desplego y verifico anteriormente en Cloud Run. El
servicio y el repositorio de Artifact Registry se eliminaron despues de la
prueba para evitar consumo innecesario. El proyecto de Google Cloud se conserva:

```text
Proyecto: asistente-anh-demo-3011h
Region propuesta: us-central1
```

La integracion actual agrega dos servicios simulados independientes:

```text
Asistente web y RAG       puerto 8080
Backend ANH simulado      puerto 8001
Ciudadania Digital        puerto 8002
```

## Alternativas de despliegue

| Alternativa | Ventajas | Riesgos o esfuerzo | Uso recomendado |
| --- | --- | --- | --- |
| Ejecucion local con Docker Compose | Menor latencia, datos estables durante la sesion y depuracion sencilla. | Requiere Docker y un equipo encendido. | Desarrollo, reunion y grabacion. |
| Un servicio Cloud Run con tres contenedores | Una sola URL publica; los mocks permanecen internos y pueden comunicarse por `localhost`. | Requiere construir tres imagenes y una configuracion multikontenedor. | Prueba remota temporal. |
| Tres servicios Cloud Run | Desacoplamiento y escalamiento independiente. | Requiere URLs, IAM, tokens de identidad y mayor operacion. | Evolucion posterior, no necesaria para el MVP. |

La alternativa recomendada para una prueba remota es un servicio Cloud Run con
tres contenedores. La decision debe confirmarse en la reunion del equipo.

## Arquitectura propuesta

```text
Internet
   |
   v
Cloud Run: asistente-anh-demo
   |-- Asistente web, ingreso publico en 8080
   |-- Backend ANH, acceso interno en localhost:8001
   `-- Ciudadania Digital, acceso interno en localhost:8002
```

Solo el asistente recibe trafico externo. Los mocks no deben exponerse
publicamente. La aplicacion se inicia con `BACKEND_MODE=http`.

## Entornos

| Entorno | Proposito | Datos | Disponibilidad |
| --- | --- | --- | --- |
| Desarrollo local | Implementacion y pruebas unitarias. | Datos ficticios y archivos temporales. | Bajo demanda. |
| Integracion local | Flujo completo con Docker Compose. | Semillas del repositorio de servicios externos. | Durante pruebas del equipo. |
| Demo en Cloud Run | Acceso remoto y evidencia de ejecucion. | Solo datos ficticios. | Ventana corta previamente coordinada. |
| Produccion futura | Servicio institucional hipotetico. | Requeriria controles y almacenamiento administrado. | Fuera del alcance del MVP. |

## Preparacion requerida

1. Aprobar los contratos OpenAPI y sus formatos de datos.
2. Mantener verde la suite de pruebas del asistente y de los mocks.
3. Construir una imagen para cada componente.
4. Publicar temporalmente las imagenes en Artifact Registry.
5. Definir la configuracion multikontenedor y el orden de inicio.
6. Configurar `min-instances=0` y `max-instances=1`.
7. Validar el flujo completo desde la URL publica.
8. Eliminar Cloud Run y Artifact Registry cuando termine la ventana de prueba.

## Seguridad y privacidad

- Utilizar exclusivamente identidades, fotografias y solicitudes ficticias.
- Publicar solamente el contenedor del asistente.
- Mantener los mocks accesibles dentro de la instancia.
- No almacenar claves en el repositorio.
- Usar variables de entorno o Secret Manager si aparecen credenciales reales.
- No registrar fotografias, CI completos ni cuerpos de solicitud en logs.
- Aplicar HTTPS, proporcionado por Cloud Run, para el acceso publico.
- Mantener biometria real e integraciones gubernamentales fuera del alcance.

La cabecera `X-API-Key` de los mocks documenta el contrato, pero no representa
autenticacion productiva porque el entorno simulado acepta cualquier valor no
vacio.

## Persistencia

Backend ANH usa SQLite dentro de su contenedor. El sistema de archivos de Cloud
Run es temporal y una instancia nueva puede restaurar solamente las semillas.
Esto es aceptable para una demostracion coordinada, pero no para produccion.

Una evolucion real deberia evaluar Firestore o Cloud SQL para solicitudes y
Cloud Storage para adjuntos. Esa migracion requiere analisis de costos,
proteccion de datos, respaldos y recuperacion.

## Contingencia y recuperacion

| Evento | Respuesta inmediata | Recuperacion |
| --- | --- | --- |
| Cloud Run no inicia | Usar la ejecucion local validada. | Revisar logs, salud y variables de entorno. |
| Un mock no responde | Mostrar error controlado y detener el registro. | Reiniciar la revision o desplegar la imagen anterior. |
| Se pierden solicitudes | Informar que son datos temporales de demo. | Reiniciar desde semillas y repetir el caso. |
| La revision nueva falla | No dirigir trafico a la revision. | Volver a la revision estable anterior. |
| Aumenta el consumo | Detener la prueba. | Eliminar servicio e imagenes y revisar facturacion. |

## Criterios de liberacion

El despliegue temporal se aprueba solo cuando:

- Las pruebas automatizadas terminan sin fallos.
- Backend ANH y Ciudadania Digital responden en `/health`.
- Se completa registro, consulta y resolucion de una solicitud.
- La interfaz identifica el modo `Backend: http`.
- No se usan datos personales reales.
- Existe una persona responsable de eliminar los recursos al terminar.

## Evidencias para el documento final

- Diagrama de la arquitectura seleccionada.
- Captura de los tres componentes saludables.
- Captura del flujo completo desde la interfaz.
- Resultado de pruebas automatizadas.
- URL temporal o evidencia de una ejecucion local si no se publica.
- Registro de eliminacion de recursos despues de la prueba.

## Decisiones pendientes de la reunion

- Confirmar si la integracion HTTP entra en el alcance final.
- Confirmar si los contratos OpenAPI quedan congelados.
- Elegir demo local o despliegue temporal multikontenedor.
- Definir responsable de construccion, prueba y eliminacion del despliegue.
- Decidir si SQLite temporal es suficiente para toda la validacion academica.
