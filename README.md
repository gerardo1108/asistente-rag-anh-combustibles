# Asistente Conversacional basado en RAG para la Orientación Normada en el Registro de Combustible Líquido fuera de Tanque (ANH)

## 📌 Descripción del Proyecto
Este proyecto desarrolla un prototipo funcional de asistente conversacional inteligente basado en arquitectura **Retrieval-Augmented Generation (RAG)** y **Function Calling** (Agentes). Su objetivo es orientar a los ciudadanos en el trámite de registro para la compra de combustible líquido fuera de tanque ante la **Agencia Nacional de Hidrocarburos (ANH)** de Bolivia, mitigando errores de llenado y reduciendo alucinaciones mediante la inyección estricta del corpus normativo vigente (Decreto Supremo N° 5400 y Resoluciones Administrativas).

---

## 👥 Integrantes del Equipo (Grupo 3011H)
* **Cruz García, Johari Maharai**
* **Quintero Sandoval, Gerardo**
* **Carrasco Castilla, Carlos Alberto**
* **Pardo Salinas, Helmuth Alberto**

---

## 🏗️ Arquitectura del Sistema
El prototipo consta de tres capas principales ejecutadas en un entorno controlado de pruebas:
1. **Indexación y Recuperación (RAG Engine):** Procesamiento de la normativa oficial de la ANH en fragmentos semánticos e indexación mediante una Base de Datos Vectorial (`ChromaDB` / `FAISS`).
2. **Razonamiento y Generación (LLM):** Inyección contextual de los fragmentos normativos ($k=3$) para generar respuestas precisas con citación de artículos y abstención normada.
3. **Módulo Agéntico (Function Calling):** Extracción de parámetros en lenguaje natural para simular la consulta del estado de trámite en un entorno simulado de pruebas.

---

## 🛠️ Requisitos e Instalación

### Prerrequisitos
* Python 3.10 o superior
* Clave de API de OpenAI / Anthropic / Groq (configurada en variables de entorno)

### Pasos para ejecutar localmente

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/TU_USUARIO/asistente-rag-anh-combustibles.git](https://github.com/TU_USUARIO/asistente-rag-anh-combustibles.git)
   cd asistente-rag-anh-combustibles
   ```

2. **Crear y activar un entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Crear un archivo `.env` en la raíz del proyecto:
   ```env
   OPENAI_API_KEY=tu_api_key_aqui
   ```

5. **Indexar el corpus normativo:**
   ```bash
   python src/ingest.py
   ```

6. **Ejecutar la interfaz interactiva:**
   ```bash
   streamlit run src/app.py
   ```

---

## 📊 Evaluación del Sistema (Métricas RAG)
El prototipo incluye scripts automáticos para validar las métricas exigidas en el marco experimental:
* **Fidelidad respecto a la fuente (*Faithfulness*):** Verificación de respuestas 100% fundamentadas en la norma.
* **Precisión de Recuperación (*Context Precision & Recall*):** Extracción exacta del artículo normativo aplicable.
* **Tasa de Abstención:** Capacidad del modelo para declarar falta de información ante consultas no normadas.

Para ejecutar la suite de pruebas:
```bash
python eval/evaluate_rag.py
```

---

## 📄 Licencia y Descargo de Responsabilidad
Este proyecto se ha desarrollado exclusivamente con fines académicos para la Maestría en Inteligencia Artificial (UNIR). Las respuestas generadas por el asistente tienen carácter estrictamente orientativo y no reemplazan las decisiones administrativas oficiales dictaminadas por la ANH.
