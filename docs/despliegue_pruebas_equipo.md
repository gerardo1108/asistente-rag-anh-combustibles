# Despliegue temporal para pruebas con usuarios y equipo

## Estado y alcance

Plan de operación para la V2, actualizado el 24 de septiembre de 2026.
La prueba técnica en Compute Engine finalizó y sus recursos se eliminaron.
No existe actualmente una URL activa. Este documento no crea infraestructura.

Se comprobó una VM Linux AMD64 `e2-medium`, con 4 GiB y cuatro servicios
Docker Compose: chat, Backend ANH simulado, Ciudadanía Digital simulada y RAG.
Pasaron registro, consulta, aprobación, recuperación de adjunto sintético,
persistencia tras reiniciar los mocks y 12 consultas de validación del RAG.
La prueba fue por SSH: **no valida todavía acceso público, roles ni concurrencia**.

La próxima sesión ofrecerá acceso desde el navegador a participantes invitados
sin instalar Google Cloud CLI. Se conservarán datos ficticios hasta la evaluación
mediante respaldos locales verificados, aunque se elimine la VM entre sesiones.

## Responsabilidades propuestas

| Persona | Responsabilidad durante la sesión |
|---|---|
| Gerardo | Crear el despliegue, configurar accesos, observar recursos, respaldar y eliminar |
| Helmuth | Verificar interfaz y registro; acompañar a participantes y registrar incidencias |
| Johari | Verificar supervisión, aprobación/rechazo y seguimiento; consolidar resultados |
| Usuarios invitados | Probar chat, registro y seguimiento con identidades y fotografías ficticias provistas |

La distribución se coordina antes de cada sesión. Los compañeros no necesitan
permisos de propietario ni la clave Groq para probar la aplicación. Las cuentas
web de supervisión no equivalen a acceso SSH o administración de Google Cloud.

## Arquitectura propuesta para compartir

```text
Navegadores de participantes y equipo
                  |
             HTTPS :443
                  |
       Proxy Caddy en la misma VM
       Autenticación y control de rutas
          |       |       |       |
        chat     ANH   Ciudadanía RAG
                  |
          SQLite en volúmenes Docker
                  |
      copia consistente -> respaldo local privado
```

Una sola VM, sin GPU, Cloud SQL, balanceador administrado ni NAT Gateway.
Caddy gestionará TLS con un dominio/subdominio controlado por el equipo y DNS
apuntando a la IP de la sesión. **El dominio no está elegido ni configurado**;
no debe anunciarse un enlace hasta comprobar certificado y acceso externo.
La IP puede ser efímera; actualizar DNS al recrear la VM y comprobar propagación.

Abrir 443 y, si la emisión/redirección TLS lo necesita, 80. Restringir SSH al
operador, preferentemente mediante IAP o IP de administración. Los puertos
8001, 8002, 8003 y 8080 no deben estar abiertos a Internet; los contenedores
se comunican por la red interna de Compose.

Fuentes: [HTTPS automático de Caddy](https://caddyserver.com/docs/automatic-https),
[proxy inverso](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy),
[acceso administrativo por IAP](https://docs.cloud.google.com/iap/docs/using-tcp-forwarding).
IAP para SSH requiere permisos y reglas específicos; no queda configurado
por habilitar el acceso web ni sustituye la autenticación de participantes.

## Cambios obligatorios antes de invitar usuarios

Estos cambios **están pendientes**. El Compose local y el de prueba por túnel
no constituyen una configuración lista para publicar.

1. Añadir el proxy y reemplazar las URLs `http://hostname:8001–8003` del chat
   y supervisor por rutas del mismo origen HTTPS. Una propuesta es
   `/api/anh`, `/api/ciudadania` y `/api/rag`; retirar el prefijo en el proxy
   antes de enviarlo al servicio. Verificar también recursos estáticos.
2. Exigir autenticación en páginas y APIs, incluso entrando directamente a
   una URL. Para esta demo pequeña puede usarse autenticación básica sobre
   HTTPS, con cuentas por participante y credenciales distintas para equipo.
   Guardar únicamente hashes en la configuración privada del proxy.
3. Separar permisos por método y ruta: participantes pueden registrar y consultar
   estado; solo el equipo puede listar solicitudes, ver detalle/adjuntos y
   cambiar estado. Proteger `/supervisor` **y las APIs**, no solo ocultar botones.
   El seguimiento actual por código se limita a datos ficticios: no proporciona
   autorización por propietario para producción.
4. El proxy debe rechazar rutas no permitidas por defecto y proteger cada
   endpoint RAG para evitar consumo anónimo. Las claves `X-API-Key` escritas
   en JavaScript son demostrativas y no se pueden usar como control de acceso.
5. Establecer `PERMITIR_REINICIO=false`, bloquear `/reiniciar` desde el ingreso
   y restringir CORS al origen de la demo o eliminarlo si ya no se necesita.
6. Implementar 2 MiB por foto en servidor y cliente. Definir cantidad máxima
   según contrato y límite total de petición contemplando base64 y metadatos;
   comprobar respuestas de error y límites también en el proxy.
7. Mantener `.env` privado (600), enviar solo claves necesarias por canal seguro,
   excluirlo del contexto de construcción y no registrar cuerpos, fotos o claves.
8. Añadir arranque ordenado, comprobaciones de salud y límites de recursos;
   probar la carga esperada. Comenzar con sesiones guiadas y baja concurrencia,
   sin afirmar capacidad multiusuario basada en la prueba individual.

[Autenticación básica y hashes en Caddy](https://caddyserver.com/docs/caddyfile/directives/basic_auth).
Las pruebas negativas deben verificar 401/403 sin credenciales, denegación de
supervisión a participantes y ausencia de acceso directo a los puertos internos.

## Preparación de una sesión

1. Acordar fecha, duración, cantidad de participantes simultáneos y responsables.
   Registrar un identificador de sesión y el commit exacto a desplegar.
2. Implementar y probar los cambios anteriores localmente. Construir imágenes
   Linux AMD64; preferir construir fuera de la VM cuando haya un entorno disponible.
   Si se construye en ella, incluir tiempo de instalación y descarga en la ventana.
3. Crear una VM `e2-medium` en `us-central1` con un disco estándar de 30 GiB como
   punto inicial para esta demo desechable. Validar capacidad con las imágenes
   reales; no confundir tamaño de disco con almacenamiento usado.
4. Etiquetar todos los recursos con la sesión y anotar su inventario privado.
   Usar cuenta de servicio sin permisos innecesarios o ninguna si no se necesita.
5. Configurar un máximo inicial de cuatro horas y acción `STOP` como protección
   ante olvido. El operador sigue siendo responsable de respaldar y eliminar.
   El tiempo incluye preparación: ajustar la ventana antes de invitar al equipo.
6. Restaurar una copia verificada o iniciar desde semillas, según el objetivo.
   Restaurar con escritores detenidos, permisos correctos y versión compatible.
   No mezclar las bases locales de desarrollo con las de la sesión.
7. Configurar DNS, TLS y cuentas privadas. Iniciar contenedores y esperar a que
   todos estén listos. El primer arranque del RAG en la prueba tardó más de un
   minuto; no enviar invitaciones únicamente porque la VM figure `RUNNING`.
8. Probar desde otra conexión a Internet: chat, recursos, registro, foto ficticia,
   supervisor autorizado, seguimiento, RAG y controles de acceso negativos.
9. Probar varios navegadores al nivel de concurrencia acordado, medir errores,
   latencia y memoria. Reducir concurrencia o ajustar capacidad si falla.
10. Compartir URL, horario y guía de prueba. Entregar credenciales por canal
    privado; nunca en GitHub, capturas públicas o enlaces con contraseñas.

[Límite de tiempo de la VM](https://docs.cloud.google.com/compute/docs/instances/limit-vm-runtime).
Un apagado automático conserva el disco y sus cargos; no elimina el despliegue.

## Guion para participantes y los dos compañeros

| Paso | Acción | Resultado a comprobar |
|---|---|---|
| Acceso | Abrir URL HTTPS y autenticarse | Chat visible sin advertencias TLS |
| Normativa | Preguntar requisitos del formulario | Respuesta orientativa con fuentes |
| Registro | Usar CI ficticio `6789012` y completar el formulario | Código de trámite y estado inicial |
| Adjunto | Usar imagen ficticia provista | Carga correcta; error claro si excede límites |
| Supervisión | Compañero autorizado revisa y aprueba un caso | Estado actualizado y adjunto accesible |
| Rechazo | Crear otro caso y rechazarlo con motivo | Motivo visible al consultar seguimiento |
| Abstención | Preguntar un dato fuera del corpus | No inventar respuesta normativa |
| Acceso restringido | Participante intenta abrir supervisión | Acceso denegado |

No usar CI, fotos ni documentos reales. El mock no hace biometría ni trámites
oficiales. Cada participante conserva el código del caso para su seguimiento.
Registrar con un alias: tarea, resultado esperado/obtenido, tiempo, error y
claridad percibida (1–5). Sanitizar capturas y comentarios antes de compartirlos.
No solicitar nombres, correos o contraseñas en el registro de incidencias público.

## Cierre y conservación hasta la evaluación

1. Avisar el cierre y detener ingreso y servicios escritores.
2. Respaldar ambas SQLite con la API de backup de SQLite. No copiar archivos
   abiertos a ciegas. Incluir versión, fecha y manifiesto SHA-256.
3. Descargar en `.local/` u otro almacenamiento privado del responsable. Mantener
   una segunda copia privada en un dispositivo o destino acordado por el equipo.
4. Verificar hashes e integridad SQLite, restaurar en un entorno aislado y
   comprobar códigos, estados y adjuntos. La comprobación de integridad sola
   no sustituye el ensayo de restauración funcional.
5. **Solo después de verificar la copia**, eliminar VM, discos de la sesión,
   IP reservada si existe y cualquier imagen/bucket creado para esa sesión.
   No borrar recursos compartidos ni datos ajenos al inventario.
6. Verificar que no quedan esos recursos, retirar DNS de la sesión, revocar
   credenciales temporales y cerrar túneles. Registrar cierre y revisar cargos.

La próxima sesión recrea la infraestructura y restaura la copia. Conservar
respaldos hasta la evaluación final; acordar luego qué evidencia retener.
No programar borrado automático de los datos antes de esa fecha.

## Costos y decisión operativa

La prioridad es pagar por sesiones, conservando copias privadas entre ellas.
Presupuestar cómputo de preparación y prueba, disco mientras exista, IPv4, salida
de red, imágenes/builds si se usan servicios adicionales, dominio y consumo Groq.
Detener Docker no detiene la facturación de la VM. Eliminar la VM no elimina
necesariamente todos los recursos independientes; usar el inventario de sesión.

Revisar tarifas antes de cada aprovisionamiento y configurar alertas. No prometer
factura cero ni que una alerta sea un límite de gasto. La prueba realizada no
midió costo facturado ni capacidad bajo concurrencia.

## Qué se publica en GitHub

Publicar esta guía, código, plantillas sin secretos, semillas ficticias y resultados
agregados revisados. El repositorio no es el lugar de entrega de credenciales.

Excluir `.env` y variantes privadas, claves, cuentas de servicio, bases SQLite,
respaldos, logs, inventarios con accesos y respuestas/capturas con datos de pruebas.
Las bitácoras locales de la sesión anterior se conservan fuera del push; el
resumen técnico sanitizado está al inicio de este documento.

`.gitignore` no retira archivos ya versionados ni limpia secretos del historial.
Antes de cada push: revisar `git status`, archivos staged y diff; comprobar que
las exclusiones aplican. Si aparece una clave en un commit, revocarla y resolver
su exposición antes de publicar. No excluir todas las guías por contener detalles
técnicos: separar documentación compartible y datos operativos privados.
