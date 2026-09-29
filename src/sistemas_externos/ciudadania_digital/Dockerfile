FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY semillas ./semillas

EXPOSE 8002

CMD ["uvicorn", "sistemas_externos.ciudadania_digital.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8002"]
