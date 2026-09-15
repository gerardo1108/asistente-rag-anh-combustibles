# Guion de demo y video

## Objetivo del video

Demostrar en menos de 5 minutos que el MVP atiende la observacion de la Entrega
2: aplica Lean, usa metricas, tiene criterios de decision y muestra un prototipo
funcional acotado al registro para consumo de combustibles fuera de tanque.

## Preparacion

Ejecutar el prototipo:

```bash
APP_PORT=8002 python3 src/app.py
```

Abrir:

```text
http://127.0.0.1:8002
```

Ejecutar pruebas antes de grabar:

```bash
python3 -m unittest discover -s tests
python3 eval/evaluate_rag.py --mode both
```

## Estructura sugerida

| Tiempo | Que mostrar | Mensaje clave |
| --- | --- | --- |
| 0:00-0:30 | README o pantalla inicial del prototipo | El alcance esta acotado al tramite ANH para combustible fuera de tanque. |
| 0:30-1:10 | Consulta normativa en el chat | El asistente responde en lenguaje claro y muestra fuentes recuperadas. |
| 1:10-2:30 | Registro guiado completo | El flujo valida CI, zona, combustible, volumen, destino y fotografia simulada. |
| 2:30-3:10 | Panel evaluador simulado | La solicitud queda pendiente y el evaluador ve detalle suficiente para decidir. |
| 3:10-3:40 | Consulta de estado por codigo y CI | El usuario puede consultar seguimiento desde el chat o el bloque lateral. |
| 3:40-4:20 | Metricas y pruebas | Se muestran 15 pruebas OK y evaluacion RAG con top-3 y abstencion al 100%. |
| 4:20-5:00 | Decision Lean | Se explica que se congela alcance y se deja biometria real fuera por tiempo, riesgo y alcance academico. |

## Flujo exacto para grabar

Consulta normativa:

```text
Que necesito para registrarme como consumidor de combustible en bidon?
```

Registro:

```text
iniciar registro
1234567
Agricultura
nacional
gasolina
20
Bomba de agua
adjunto foto ci
si
```

Consulta de estado desde chat:

```text
Quiero consultar el estado de ANH-XXXXXXXX con CI 1234567
```

Usar el codigo real generado por la interfaz.

## Narracion breve

Este prototipo corresponde al MVP del asistente RAG ANH. El alcance se limita al
registro simulado para consumo de combustible liquido fuera de tanque. Primero
mostramos que el asistente responde consultas normativas en lenguaje claro y con
fuentes recuperadas del corpus. Si no hay evidencia suficiente, el sistema debe
abstenerse.

Luego ejecutamos el registro guiado. El flujo valida identidad simulada,
actividad, zona, combustible, volumen permitido, destino de uso y evidencia
fotografica simulada. La fotografia no usa biometria real; solo comprueba que el
prototipo no avanza sin una evidencia controlada de prueba.

Despues de registrar la solicitud, el panel evaluador simulado permite revisar
el detalle y cambiar el estado a pendiente, aprobada o rechazada. Finalmente, el
usuario puede consultar el estado desde el chat usando codigo y CI.

La evaluacion Lean compara este MVP contra un flujo manual sin asistencia
conversacional. Las metricas actuales cumplen los umbrales definidos: top-3 y
abstencion del RAG al 100% y 15 pruebas funcionales correctas. Por eso la
decision del equipo es congelar nuevas funcionalidades, no implementar biometria
real en esta etapa y concentrarse en validacion, evidencia y presentacion final.

## Evidencias disponibles

- `docs/evidencias/demo_registro_panel.png`: registro completo con panel evaluador.
- `docs/evidencias/demo_consulta_estado_chat.png`: consulta de estado desde el chat.

## Riesgos a mencionar

- Ciudadania Digital y ANH son integraciones simuladas.
- No hay autenticacion productiva ni base de datos real.
- La validacion fotografica es controlada y no biometrica.
- El siguiente aprendizaje debe venir de un piloto breve con usuarios reales o
  companeros de prueba.
