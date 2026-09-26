# Checklist del piloto v0.2.1

Esta lista prepara la ejecución del paquete de pruebas `Paquete_pruebas_MVP_V2.docx` y el registro `Registro_validacion_MVP_V2.xlsx`. La versión de referencia es el commit `f8b2ec3` de la rama `plan/persistencia-demo`.

## Comprobaciones ya realizadas

- [x] La rama local está sincronizada con `origin/plan/persistencia-demo`.
- [x] El árbol de trabajo está limpio.
- [x] El corpus normativo de referencia está presente.
- [x] Están presentes las semillas de titulares y solicitudes.
- [x] Están presentes los catálogos de actividades y ubicaciones.
- [x] Están presentes las rutas de interfaz ciudadana y supervisora.
- [x] `RAG_K_RESULTADOS` tiene valor predeterminado `3`.
- [x] `RAG_UMBRAL_SIMILITUD` tiene valor predeterminado `0.40`.
- [x] `scripts/cloud/tunnel.sh` pasa la validación de sintaxis.
- [x] `scripts/cloud/smoke_test.py` pasa la compilación sintáctica.

## Comprobaciones pendientes en la VM

- [ ] Confirmar que la VM corresponde al proyecto, zona e instancia autorizados.
- [ ] Confirmar que la imagen desplegada corresponde al commit `f8b2ec3`.
- [ ] Definir el proveedor LLM y registrar la configuración usada en la sesión.
- [ ] Levantar los servicios con `scripts/cloud/compose.test.yml`.
- [ ] Confirmar que los servicios solo escuchan en `127.0.0.1` dentro de la VM.
- [ ] Abrir el túnel SSH con variables explícitas, sin valores quemados.
- [ ] Confirmar que cargan las interfaces ciudadana y supervisora.
- [ ] Confirmar que funcionan los CI sintéticos `6789012` y `4521987`.
- [ ] Confirmar que funcionan las dos tarjetas de registro y la imagen sintética.
- [ ] Confirmar que el registro genera código y que `Ver estado` devuelve el estado esperado de prueba.
- [ ] Ejecutar `python scripts/cloud/smoke_test.py` y archivar su JSON de evidencia.

## Preparación de la sesión piloto

- [ ] Mantener separada la clave de respuestas del material entregado a participantes.
- [ ] Asignar IDs anónimos y orden `AB` o `BA` antes de cada sesión.
- [ ] Preparar una fila por participante y condición en `Tareas usuarios`.
- [ ] Preparar una fila por ejecución en `Consultas RAG`.
- [ ] Registrar fecha, versión, proveedor LLM y URL de sesión.
- [ ] Verificar que las capturas o videos incluyan versión y fecha.
- [ ] No usar datos personales reales ni solicitar fotografías personales.
- [ ] No completar datos faltantes con valores inventados.

## Cierre de la prueba

- [ ] Separar resultados del flujo manual A y del prototipo B.
- [ ] Calcular proporciones solo cuando exista el denominador correspondiente.
- [ ] Evaluar Q01–Q08 por pertinencia, fidelidad y recuperación top 3 cuando aplique.
- [ ] Evaluar Q09–Q12 por abstención correcta.
- [ ] Registrar incidencias, abandonos, sustituciones y reinicios.
- [ ] Revisar el registro con dos personas cuando sea posible y documentar desacuerdos.
- [ ] Copiar las evidencias al directorio de evidencias sin incluir secretos.

## Criterio de salida

El piloto puede comenzar cuando todas las comprobaciones pendientes en la VM estén marcadas, el smoke test sea satisfactorio y la configuración quede asociada al commit `f8b2ec3`. Los resultados del piloto deben incorporarse después de la ejecución, nunca antes.
