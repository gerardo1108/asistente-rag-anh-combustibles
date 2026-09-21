FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY semillas ./semillas

EXPOSE 8001

CMD ["uvicorn", "sistemas_externos.backend_anh.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8001"]
