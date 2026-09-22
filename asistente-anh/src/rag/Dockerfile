FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements-rag.txt ./
# Instala primero la distribución CPU oficial, para no arrastrar CUDA.
RUN pip install --no-cache-dir torch==2.14.0+cpu --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements-rag.txt \
    && python -c "import torch; assert torch.version.cuda is None, 'Se esperaba PyTorch CPU'"

COPY src/rag ./src/rag

# Construye el índice en la imagen: el corpus es contenido versionado y así
# el contenedor arranca sin descargar el modelo de embeddings ni reindexar.
RUN cd src && python -m rag.ingest

# El modelo ya se descargó durante la ingesta; no consultar Hugging Face al arrancar.
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

EXPOSE 8003

CMD ["uvicorn", "rag.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8003"]
