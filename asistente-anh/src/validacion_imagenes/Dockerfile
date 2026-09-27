FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements-validacion-imagenes.txt ./
RUN pip install --no-cache-dir -r requirements-validacion-imagenes.txt

COPY src ./src

EXPOSE 8004

CMD ["uvicorn", "validacion_imagenes.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8004"]
