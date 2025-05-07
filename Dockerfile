FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Открываем порт для Flask
EXPOSE ${PORT:-8080}

ENV PORT=8080

CMD ["python", "wsgi.py"] 