FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements-rag.txt ./
RUN pip install --no-cache-dir -r requirements-rag.txt

COPY src ./src
COPY catalogos ./catalogos

# Construye el índice en la imagen: el corpus es contenido versionado y así
# el contenedor arranca sin descargar el modelo de embeddings ni reindexar.
RUN cd src && python -m rag.ingest

EXPOSE 8003

CMD ["uvicorn", "rag.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8003"]
