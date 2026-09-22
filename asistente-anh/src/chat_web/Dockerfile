FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/chat_web ./src/chat_web
COPY catalogos ./catalogos
COPY recursos ./recursos

EXPOSE 8080
CMD ["uvicorn", "chat_web.server:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8080"]
