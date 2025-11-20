FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "app.core.cel.celery_app", "worker", "--loglevel=info"]
