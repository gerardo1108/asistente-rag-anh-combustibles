# Persistencia de la demo en Google Cloud

Estado: propuesta de arquitectura; no se han creado recursos ni migrado datos.
Base funcional: `v0.2.1`.

> Actualización posterior: se validó y retiró una VM de prueba. Para próximas
> sesiones se propone recrear la VM y conservar respaldos privados locales.
> Ver el [plan vigente para el equipo](despliegue_pruebas_equipo.md).
> El contenido siguiente conserva la comparación de alternativas previa.

## Requisito confirmado

El usuario eligió conservar **las solicitudes y fotografías de prueba durante
el proyecto y hasta la evaluación final**. Deben sobrevivir a reinicios,
actualizaciones de contenedores y periodos sin demostraciones. La fecha de
la evaluación y la fecha de cierre aún no están definidas en esta propuesta.
No se configura un borrado automático por antigüedad que pueda adelantarse a
la evaluación. El cierre requiere revisar qué evidencia se conserva y retirar
los recursos de forma explícita.

## Estado del código

- Backend ANH: SQLite; guarda datos, estado, motivo, clave de idempotencia y
  adjuntos codificados en base64 dentro de la columna `adjuntos_json`.
- Ciudadanía Digital: otra SQLite con titulares ficticios de prueba.
- Compose local: volúmenes separados; la conservación de cinco solicitudes
  tras recrear contenedores ya fue comprobada.
- RAG: corpus versionado e índice Chroma construido en la imagen; se puede
  reconstruir desde código y corpus. No almacena las solicitudes.
- La interfaz permite cargar imágenes, pero no aplica actualmente un límite
  de tamaño en bytes ni el backend tiene un límite explícito por adjunto.

## Recomendación para esta etapa: decisión pendiente

**Una VM temporal de Compute Engine con Docker Compose y un disco persistente
para datos.** Es una recomendación por menor cambio de código y continuidad
con la demo validada, no una afirmación de que sea la opción de menor factura
para cualquier patrón de uso. Cloud Run sigue siendo alternativa si se prefiere
adaptar el almacenamiento para operación sin servidor.

Si la prioridad es mantener un enlace disponible para visitas ocasionales sin
horarios acordados, evaluar primero **Cloud Run con almacenamiento externo**.
Si la prioridad es publicar pronto para sesiones programadas, evaluar una
**VM que se detenga entre sesiones**. Comparar ambos presupuestos antes de
elegir; no se ha aprobado ni implementado ninguna de estas arquitecturas.

Propuesta de funcionamiento:

1. Una sola VM ejecuta chat, ambos mocks y RAG CPU.
2. Un disco de datos separado contiene las dos bases SQLite. Configurar los
   montajes de Compose de forma explícita sobre ese disco; no confiar solo en
   volúmenes anónimos ni en rutas dentro de la imagen.
3. Configurar el disco de datos para conservarlo al eliminar la VM. Parar una
   VM no equivale a eliminar sus discos. Los discos persistentes están diseñados
   para conservar datos independientemente del proceso o contenedor.
4. Mantener una sola instancia escritora de cada mock. Esta propuesta no ofrece
   alta disponibilidad ni escalado horizontal de SQLite.
5. Encender la VM para las sesiones de prueba y evaluación; detenerla cuando
   no se necesite. Durante ese periodo la aplicación estará fuera de línea.

[Discos persistentes y tipos de almacenamiento](https://docs.cloud.google.com/compute/docs/disks).

Para presupuestar inicialmente, considerar una VM de **2 vCPU y 4 GiB**, sujeta
al ensayo de la arquitectura seleccionada. El RAG se probó con 1 CPU y 2 GiB;
la VM completa necesita además margen para sistema operativo, Docker y otros
servicios. Las mediciones existentes son ARM64 locales; falta validar la imagen
para la plataforma que se despliegue. Construir las imágenes fuera de la VM
pequeña de demostración evita dimensionarla para la compilación.

## Datos y retención

| Elemento | Ubicación propuesta | Conservación |
|---|---|---|
| Solicitudes, estados y fotos de prueba | SQLite ANH en disco de datos | Durante el proyecto y hasta evaluación final |
| Titulares ficticios | SQLite Ciudadanía en el mismo disco, archivo separado | Mismo periodo; semillas versionadas para recuperación |
| Corpus e índice Chroma | Imagen del RAG y corpus en Git | Versionados; índice reconstruible |
| Copias de las bases | Bucket privado de respaldo separado | Política propuesta: últimas 7 copias diarias y una previa a la evaluación |
| Clave Groq | Secreto de despliegue, fuera de imágenes y Git | Mientras opere la demo |

La política de siete copias es una propuesta operativa, no una regla ya
activada. Al terminar el proyecto, decidir explícitamente qué copia final se
conserva y cuándo retirar disco y respaldos. No se propone usar datos reales.

## Respaldo y restauración

- Crear una copia consistente de cada SQLite mediante su API de backup, o con
  los servicios escritores detenidos. No copiar a ciegas archivos abiertos.
- Respaldar al cerrar cada sesión de demo, antes de una actualización y, si se
  mantiene encendido varios días, diariamente. Guardar ambas bases juntas con
  versión de aplicación, fecha y sumas de verificación.
- Subir las copias a un bucket privado; el bucket almacena backups, no una
  base SQLite activa montada como sistema de archivos.
- Ensayar restauración en un entorno aislado: verificar integridad SQLite,
  conteo, códigos, estados y hashes de adjuntos; después consultar una solicitud
  y su fotografía desde el supervisor.
- Objetivo propuesto de pérdida máxima: desde el último respaldo completado.
  Objetivo de recuperación: una sesión de trabajo del equipo, por medir.

El reinicio `/reiniciar` de los mocks elimina datos y recarga semillas: debe
estar deshabilitado en la demo persistente (`PERMITIR_REINICIO=false`).
Asimismo, no usar `docker compose down -v` como procedimiento de actualización.

## Alternativas

| Opción | Ventaja para el proyecto | Trabajo o costo a considerar |
|---|---|---|
| Compute Engine + SQLite en disco | Conserva código y flujo actuales | Administración de VM, backups, cómputo mientras está encendida y almacenamiento persistente |
| Cloud Run + Firestore + Cloud Storage | Persistencia externa y servicios que pueden escalar a cero | Reescribir almacenes, transacciones/idempotencia, consultas y manejo de adjuntos |
| Cloud Run + Cloud SQL | Base relacional administrada | Migración SQLite a PostgreSQL/MySQL y costo de instancia/almacenamiento |

Cloud Run no conserva el sistema de archivos local tras terminar una instancia.
Por ello, poner las SQLite actuales dentro del contenedor no satisface el requisito.
[Contrato de ejecución](https://docs.cloud.google.com/run/docs/container-contract).

Tampoco se propone montar SQLite activa sobre Cloud Storage FUSE: Google
advierte que no proporciona bloqueo de archivos para escrituras concurrentes
ni semántica POSIX completa. Esa limitación hace inadecuado este atajo para
las bases actuales.
[Limitaciones del montaje](https://docs.cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts).

Si se elige Firestore, guardar metadatos en documentos y las imágenes como
objetos separados: los documentos tienen un límite de 1 MiB. Migrar los
adjuntos base64 actuales directamente a documentos no es una solución general.
[Límites de Firestore](https://docs.cloud.google.com/firestore/quotas).

## Control del crecimiento y costos

### Consumo medido frente a capacidad contratada

La VM no reduce el trabajo del RAG: aloja los mismos servicios y añade el
sistema operativo y Docker. Los **4 GiB sugeridos son capacidad para presupuestar
y probar el conjunto**, no consumo medido ni requisito definitivo. El RAG solo
registró una mediana RSS de 1204 MiB tras consulta y un pico cgroup de 1299 MiB,
con un límite de 2 GiB. No se midió el conjunto bajo concurrencia en Google Cloud.
Ver [método y límites de la medición local](optimizacion_rag_cpu.md).

En una VM encendida se factura la capacidad asignada aunque el chat no reciba
visitas. Detenerla interrumpe el servicio y el cobro de cómputo; los discos y
otros recursos retenidos pueden seguir generando cargos.
[Comportamiento al detener Compute Engine](https://docs.cloud.google.com/compute/docs/reference/rest/v1/instances/stop).

### Comparación por patrón de uso

| Criterio | VM con horario limitado | Cloud Run con persistencia externa |
|---|---|---|
| Uso previsto | Reuniones, pruebas y evaluación programadas | Visitas ocasionales en cualquier momento |
| Disponibilidad | Fuera de línea cuando la VM está detenida | Una solicitud puede activar una instancia desde cero |
| Cómputo sin visitas | Se cobra si se deja encendida | Puede escalar a cero con mínimo de instancias en cero |
| Datos hasta la evaluación | SQLite en disco persistente y respaldos | Firestore para registros y Cloud Storage para fotos, como alternativa propuesta |
| Cambios de aplicación | Montajes, configuración y operación de Compose | Adaptar persistencia, adjuntos, consultas e idempotencia |
| Operación | Arranque/parada, mantenimiento del sistema y backups | Configurar escalado, permisos, almacenamiento y recuperación |
| Latencia inicial | Encender y comprobar servicios antes de la sesión | Puede haber espera por arranque en frío |
| Costos que permanecen | Discos, respaldos, imágenes y otros recursos retenidos | Almacenamiento, operaciones, imágenes y otros servicios utilizados |

Para evaluar Cloud Run con uso esporádico, proponer facturación basada en
solicitudes, mínimo de instancias en cero y un máximo ajustado a pruebas de
capacidad. Escalar a cero no implica factura total cero ni elimina el costo de
almacenar los datos. La primera visita puede esperar el arranque del RAG; los
7,098 s medidos localmente no predicen ese tiempo en Cloud Run.
[Escalado y arranque desde cero](https://docs.cloud.google.com/run/docs/about-instance-autoscaling),
[modalidades de facturación](https://cloud.google.com/run/pricing).

### Escenarios que se deben presupuestar

1. **VM por sesiones:** como ejemplo ilustrativo, 10 sesiones de 2 horas suman
   20 horas, más preparación y respaldos. El disco se conserva todo el mes.
2. **VM continua:** un mes de 30 días encendida suma 720 horas. Esto representa
   36 veces las horas del ejemplo de 20 horas, no 36 veces la factura total,
   porque hay costos de almacenamiento y otros componentes.
3. **Cloud Run ocasional:** estimar solicitudes y tiempo facturable de cada
   servicio, CPU/memoria asignadas, operaciones de base de datos, tamaño de
   fotos, red y respaldos. El número de visitas por sí solo no determina el costo.

No se asignan importes ni se garantiza una opción más barata: faltan región,
duración del proyecto, horas de disponibilidad, volumen y concurrencia esperados.
Incluir también construcción y registro de imágenes, registros de operación,
secretos y uso del proveedor Groq cuando corresponda. Separar costo de nube
del esfuerzo de migración y mantenimiento. Referencias consultadas el 22 de
septiembre de 2026; verificar tarifas al elaborar el presupuesto.

### Límite de adjuntos

Antes de exponer la demo, proponer un límite de **2 MiB por foto**, validado en
cliente y servidor, además de un máximo de petición. No está implementado en
v0.2.1. La política concreta de cantidad de adjuntos debe respetar los contratos.

Ejemplo de capacidad, no previsión de uso: 1000 solicitudes con una foto de
2 MiB equivalen a unos 2,60 GiB solo para sus representaciones base64 (4/3 del
tamaño original), antes de metadatos, páginas SQLite, espacio libre y respaldos.
La cuota y el tamaño de disco se eligen con el volumen esperado, no solo con
las cinco solicitudes de prueba actuales.

Modelo para estimar, sin asignar una cifra monetaria todavía:

`costo = horas encendida × tarifa VM + discos provisionados + backups + imágenes + red + otros servicios utilizados`

Detener la VM reduce el cómputo pero no elimina cargos de recursos retenidos;
revisar también direcciones IP, discos e imágenes. No se asume gratuidad por
usar poco el chat o por disponer de créditos académicos.
[Facturación al detener una VM](https://docs.cloud.google.com/compute/docs/reference/rest/v1/instances/stop).

## Preparación pendiente antes del despliegue

1. Definir región, duración, disponibilidad y número esperado de solicitudes/fotos;
   presupuestar VM por sesiones y Cloud Run con almacenamiento externo.
2. Elegir la arquitectura comparando factura, esfuerzo de adaptación y tiempo
   de arranque aceptable para los evaluadores.
3. Preparar montajes persistentes, backups y prueba de restauración local.
4. Adaptar URLs locales a rutas HTTPS y un punto de entrada; los puertos 8001–8003
   no deben quedar expuestos como sustituto de autenticación. Restringir acceso
   al supervisor: las claves actuales son demostrativas.
5. Verificar arquitectura de imagen, secretos y arranque antes de aprovisionar.

No hay cambios en los contenedores actuales, nuevas dependencias ni costos GCP
por esta fase de documentación.
