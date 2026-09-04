# Asistente conversacional basado en arquitectura RAG para la orientación normativa ante la ANH

## Descripcion del Proyecto
Este proyecto desarrolla un prototipo funcional de asistente conversacional inteligente basado en arquitectura **Retrieval-Augmented Generation (RAG)** y **Function Calling** (Agentes). Su objetivo es orientar a los ciudadanos en el trámite de registro para la compra de combustible líquido fuera de tanque ante la **Agencia Nacional de Hidrocarburos (ANH)** de Bolivia, mitigando errores de llenado y reduciendo alucinaciones mediante la inyección estricta del corpus normativo vigente (Decreto Supremo N° 5400 y Resoluciones Administrativas).

---

## Integrantes del Equipo (Grupo 3011H)
* **Cruz García, Johari Maharai**
* **Pardo Salinas, Helmuth Alberto**
* **Quintero Sandoval, Gerardo**


---

## Estado actual del prototipo
Esta version inicial implementa un MVP ejecutable sin dependencias externas, pensado para ponerse al dia rapidamente y demostrar el flujo academico principal:

1. Chat conversacional para consultas normativas y registro guiado.
2. Recuperacion trazable sobre un corpus curado.
3. Registro simulado de solicitud con verificacion de Carnet de Identidad.
4. Validacion determinista del volumen declarado segun zona nacional o fronteriza.
5. Consulta de estado de tramite.
6. Panel evaluador ANH simulado para aprobar, rechazar o dejar pendiente una solicitud.
7. Evaluacion tecnica inicial del recuperador con un set de preguntas controladas.

La capa RAG actual es lexica y offline para facilitar la demostracion. El siguiente paso tecnico es reemplazar o complementar este recuperador con embeddings y una base vectorial (`ChromaDB` o `FAISS`), manteniendo las mismas interfaces.

---

## Arquitectura del Sistema
El prototipo se organiza en cinco capas ejecutadas en un entorno controlado de pruebas:

1. **Corpus normativo:** fragmentos curados en `data/corpus_normativo.json`.
2. **Motor RAG:** recuperador trazable en `src/rag_engine.py`.
3. **Backend simulado:** verificacion de Ciudadania Digital, solicitudes, estados y reglas de volumen en `src/backend_simulado.py`.
4. **Orquestador conversacional:** maquina de estados del registro en `src/conversation.py`.
5. **Interfaz web:** aplicacion local en `src/app.py`, implementada con `http.server` de Python para no depender de instalaciones adicionales.

---

## Requisitos e Instalacion

### Prerrequisitos
* Python 3.10 o superior.
* No se requiere clave de API para ejecutar el MVP actual.

### Pasos para ejecutar localmente

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/gerardo1108/asistente-rag-anh-combustibles.git
   cd asistente-rag-anh-combustibles
   ```

2. **Opcional: crear y activar un entorno virtual:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   source venv/bin/activate
   ```

3. **Verificar el corpus disponible:**
   ```bash
   python src/ingest.py
   ```

4. **Ejecutar la interfaz web local:**
   ```bash
   python src/app.py
   ```

5. **Abrir el navegador en:**
   ```text
   http://127.0.0.1:8001
   ```

---

## Servicio local en macOS
Para evitar ejecutar comandos manualmente despues de reiniciar el equipo, el
repositorio incluye una configuracion de `launchd`:

* `scripts/start_local_server.sh`: inicia el prototipo desde la raiz del repo.
* `infra/launchd/com.asistente-rag-anh.prototipo.plist`: define el servicio de macOS.

Una vez instalado en `~/Library/LaunchAgents`, el servidor se inicia
automaticamente al iniciar sesion y queda disponible en:

```text
http://127.0.0.1:8001
```

Los logs locales quedan en:

```text
/tmp/asistente-rag-anh-prototipo.out.log
/tmp/asistente-rag-anh-prototipo.err.log
```

---

## Evaluacion del Sistema
El prototipo incluye un set de preguntas inicial para validar la precision de recuperacion top-3:

Para ejecutar la suite de pruebas:
```bash
python eval/evaluate_rag.py
```

El objetivo minimo definido para esta etapa es alcanzar al menos 80% de recuperacion correcta sobre el set de prueba. En la version actual el set inicial obtiene 100% (5/5).

---

## Datos de prueba
Para registrar solicitudes se pueden usar estos Carnets de Identidad simulados:

* `1234567` - Ana Choque Mamani
* `7654321` - Victor Hugo Flores
* `4567890` - Rafael Quispe Condori

Los estados disponibles para el panel evaluador son `pendiente`, `aprobada` y `rechazada`.

Para probar el flujo guiado en el chat:

```text
iniciar registro
1234567
Agricultura
nacional
gasolina
20
Bomba de agua
foto ok
si
```

---

## Licencia y Descargo de Responsabilidad
Este proyecto se ha desarrollado exclusivamente con fines académicos para la Maestría en Inteligencia Artificial (UNIR). Las respuestas generadas por el asistente tienen carácter estrictamente orientativo y no reemplazan las decisiones administrativas oficiales dictaminadas por la ANH.
