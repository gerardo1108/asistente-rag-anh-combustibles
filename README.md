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
7. Evaluacion tecnica del recuperador con preguntas controladas, metricas top-1,
   top-3, MRR y abstencion en consultas fuera de alcance.
8. Pruebas funcionales del flujo conversacional para validar registro exitoso,
   entradas invalidas y prevencion de errores antes de crear solicitudes.
9. Interfaz de demostracion con indicadores del prototipo, fuentes recuperadas
   y mensajes visuales de validacion.
10. Preparacion para despliegue futuro en Google Cloud Run mediante Docker, sin
    desplegar todavia en nube.

La capa RAG actual conserva el recuperador lexico offline y agrega un modo hibrido/vectorial local basado en TF-IDF y similitud coseno. Esto permite demostrar la transicion hacia recuperacion vectorial sin depender todavia de API externa o servicios instalados. El siguiente paso tecnico es reemplazar el vectorizador local por embeddings persistidos en `ChromaDB` o `FAISS`, manteniendo las mismas interfaces.

---

## Arquitectura del Sistema
El prototipo se organiza en cinco capas ejecutadas en un entorno controlado de pruebas:

1. **Corpus normativo:** fragmentos curados en `data/corpus_normativo.json`.
2. **Motor RAG:** recuperador trazable en `src/rag_engine.py`, con modo `lexical` y modo `hybrid`.
3. **Backend simulado:** verificacion de Ciudadania Digital, solicitudes, estados y reglas de volumen en `src/backend_simulado.py`.
4. **Orquestador conversacional:** maquina de estados del registro en `src/conversation.py`.
5. **Interfaz web:** aplicacion local en `src/app.py`, implementada con `http.server` de Python para no depender de instalaciones adicionales.
   La interfaz muestra chat, fuentes recuperadas, seguimiento, panel evaluador
   e indicadores de estado del prototipo.

---

## Requisitos e Instalacion

### Prerrequisitos
* Python 3.10 o superior.
* Git instalado para clonar el repositorio.
* No se requiere clave de API para ejecutar el MVP actual.

El prototipo usa solo librerias estandar de Python, por lo que puede ejecutarse
en Windows, macOS o Linux sin instalar dependencias adicionales.

### 1. Clonar el repositorio

```bash
git clone https://github.com/gerardo1108/asistente-rag-anh-combustibles.git
cd asistente-rag-anh-combustibles
```

### 2. Crear entorno virtual opcional

#### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activacion del entorno virtual, ejecutar una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

#### Windows CMD

```bat
python -m venv venv
venv\Scripts\activate.bat
```

#### macOS o Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Verificar el corpus disponible

#### Windows

```powershell
python src/ingest.py
```

#### macOS o Linux

```bash
python3 src/ingest.py
```

### 4. Ejecutar la interfaz web local

#### Windows

```powershell
python src/app.py
```

#### macOS o Linux

```bash
python3 src/app.py
```

### 5. Abrir el navegador

```text
http://127.0.0.1:8001
```

Si el puerto `8001` esta ocupado, se puede usar otro puerto.

#### Windows PowerShell

```powershell
$env:APP_PORT="8002"
python src/app.py
```

#### macOS o Linux

```bash
APP_PORT=8002 python3 src/app.py
```

Luego abrir:

```text
http://127.0.0.1:8002
```

### Modo del recuperador RAG

Por defecto la interfaz usa el motor hibrido. Para comparar con el recuperador
lexico original:

#### Windows PowerShell

```powershell
$env:RAG_MODE="lexical"
python src/app.py

$env:RAG_MODE="hybrid"
python src/app.py
```

#### macOS o Linux

```bash
RAG_MODE=lexical python3 src/app.py
RAG_MODE=hybrid python3 src/app.py
```

### Prueba rapida de funcionamiento

En el chat del navegador se puede ejecutar este flujo:

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

Tambien se pueden probar preguntas normativas:

```text
Que necesito para registrarme como consumidor de combustible en bidon?
Tengo que subir una foto con mi carnet?
Cuantos litros puedo declarar en zona fronteriza?
La respuesta del asistente reemplaza una decision oficial de la ANH?
```

### Validar desde terminal

#### Windows

```powershell
python eval/evaluate_rag.py --mode both
python -m unittest discover -s tests
```

#### macOS o Linux

```bash
python3 eval/evaluate_rag.py --mode both
python3 -m unittest discover -s tests
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
El prototipo incluye un set de preguntas controladas para validar la recuperacion
de evidencia normativa y la abstencion ante consultas fuera de alcance. Cada
caso define la consulta, categoria, fuente esperada y fragmento esperado del
corpus cuando aplica.

Para ejecutar la suite de pruebas:
```bash
python eval/evaluate_rag.py
```

Para comparar el recuperador lexico y el hibrido:

```bash
python eval/evaluate_rag.py --mode both
```

Para generar un reporte JSON reutilizable en anexos o evidencias:

```bash
python eval/evaluate_rag.py --mode both --report eval/evaluation_report.json
```

Metricas calculadas:

* **Precision general:** porcentaje total de casos correctos, combinando
  recuperacion esperada y abstencion esperada.
* **Precision top-1:** porcentaje de consultas donde el fragmento esperado queda
  en el primer resultado.
* **Precision top-3:** porcentaje de consultas donde el fragmento esperado
  aparece entre los tres primeros resultados.
* **MRR:** promedio del inverso del ranking de la evidencia correcta; favorece
  los casos donde la fuente esperada aparece mas arriba.
* **Precision de abstencion:** porcentaje de consultas fuera de alcance donde
  el asistente no recupera evidencia y evita responder sin sustento.
* **Precision por categoria:** permite observar desempeno por tipo de consulta:
  requisitos, documentacion, seguimiento, validacion, seguridad e integracion.

El objetivo minimo definido para esta etapa es alcanzar al menos 80% de
recuperacion correcta top-3 sobre el set de prueba.

La validacion formal del prototipo esta documentada en:

```text
docs/validacion_prototipo.md
```

La guia de despliegue planeado en Google Cloud Run esta documentada en:

```text
docs/despliegue_google_cloud.md
```

### Pruebas funcionales del flujo
La suite funcional simula conversaciones completas sin abrir el navegador. Cubre
registro exitoso, CI inexistente, zona invalida, combustible invalido, volumen no
numerico, volumen excedido, fotografia no valida, cancelacion y consulta
normativa con fuentes, ademas de abstencion ante consulta fuera de alcance.

Para ejecutarla:

```bash
python -m unittest discover -s tests
```

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
