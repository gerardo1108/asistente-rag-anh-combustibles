# Análisis de preproducción y producción

## Estado actual

El despliegue temporal descrito en
`docs/despliegue_demo_v030_google_cloud_nipio.md` es una **demo pública**, no
un entorno de preproducción ni de producción.

- VM temporal `e2-medium` en Google Cloud.
- Docker Compose y SQLite.
- Caddy con HTTPS mediante `nip.io`.
- Servicios ANH y Ciudadanía Digital simulados.
- Datos sintéticos.
- Acceso público sin autenticación durante la ventana de pruebas.
- RAG y validación de imágenes dependientes de proveedores externos.
- La etiqueta `v0.3.0` conserva el corpus AGETIC que fue retirado después en
  la corrección `11ccb6d`.

Este entorno no debe recibir datos reales ni utilizarse para trámites oficiales.

## Requisitos para preproducción

### 1. Versión candidata congelada

- Definir un commit posterior a las correcciones del corpus RAG.
- Eliminar o aislar documentos normativos fuera del ámbito ANH.
- Ejecutar y registrar pruebas automatizadas, RAG, flujo completo, imágenes y
  supervisión.
- Conservar resultados reproducibles asociados al commit desplegado.

### 2. Entorno separado

- Usar un proyecto o cuenta de Google Cloud separada de desarrollo.
- Usar un dominio controlado por el equipo, no `nip.io`.
- Mantener HTTPS administrado y renovación comprobada.
- Separar variables, secretos, bases y respaldos del entorno de desarrollo.
- Usar únicamente datos sintéticos o datos anonimizados autorizados.

### 3. Persistencia y recuperación

- Migrar SQLite a PostgreSQL/Cloud SQL u otra base administrada adecuada.
- Usar almacenamiento privado para fotografías y adjuntos.
- Configurar backups automáticos.
- Probar restauración funcional, no solo integridad de archivos.
- Definir retención, eliminación y recuperación de datos.

### 4. Seguridad

- Implementar autenticación real para ciudadanos y supervisores.
- Aplicar autorización por rol en APIs, no solo ocultar botones.
- Proteger los endpoints de supervisión y reinicio.
- Restringir CORS al origen autorizado.
- Establecer límites de tamaño, frecuencia y concurrencia.
- Almacenar claves en Secret Manager o mecanismo equivalente.
- Evitar CI, fotografías, tokens y cuerpos completos en logs.
- Escanear dependencias e imágenes de contenedor.
- Ejecutar pruebas de configuración y vulnerabilidades.

### 5. Integraciones

- Sustituir los mocks de ANH y Ciudadanía Digital por servicios institucionales
  autorizados o entornos oficiales de prueba.
- Aprobar contratos, autenticación, errores, timeouts y trazabilidad.
- Confirmar jurídicamente el uso de identidad y fotografías.
- Determinar qué validación de imágenes es oficialmente aceptable.

### 6. Operación

- Configurar health checks y readiness checks.
- Monitorear errores, latencia, cuotas y consumo.
- Configurar alertas de disponibilidad y costos.
- Definir rollback y recuperación ante fallos.
- Asignar responsables de soporte y mantenimiento.
- Establecer ventanas de mantenimiento y objetivos de disponibilidad.

## Requisitos adicionales para producción

Además de los controles de preproducción, se requiere:

- Aprobación formal de ANH y de las entidades integradas.
- Revisión legal de protección de datos personales y fotografías.
- Evaluación de impacto de privacidad.
- Política de consentimiento, acceso, corrección y eliminación.
- Alta disponibilidad y recuperación ante desastres.
- Pruebas de carga, concurrencia y degradación controlada.
- Pruebas de seguridad independientes.
- Control de versiones y aprobación formal de cambios.
- Registro de auditoría.
- Acuerdos de nivel de servicio.
- Presupuesto operativo para nube, APIs, almacenamiento y soporte.
- Plan de continuidad y respuesta a incidentes.

## Orden recomendado

1. Corregir y congelar el corpus y la versión candidata.
2. Crear un entorno de preproducción separado.
3. Sustituir SQLite por persistencia administrada.
4. Implementar autenticación y autorización por roles.
5. Integrar servicios institucionales de prueba.
6. Ejecutar pruebas funcionales, de seguridad, carga y recuperación.
7. Obtener aprobación académica, técnica, legal e institucional.
8. Desplegar producción con monitoreo, auditoría y rollback.

## Brecha principal

La brecha principal no está en la interfaz. Está en la identidad institucional,
la persistencia, la seguridad, la privacidad, la operación y la sustitución de
los servicios simulados. Hasta cerrar esas brechas, el sistema debe presentarse
como prototipo académico o demo controlada.
