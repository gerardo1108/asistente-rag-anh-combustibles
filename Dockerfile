FROM python:3.12-slim

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8080
ENV RAG_MODE=hybrid
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# El MVP actual usa solo librerias estandar de Python. No se instala
# requirements.txt porque contiene dependencias previstas para fases futuras.
COPY data ./data
COPY src ./src

EXPOSE 8080

CMD ["python", "src/app.py"]
