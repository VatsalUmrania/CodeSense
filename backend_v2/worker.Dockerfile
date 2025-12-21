FROM python:3.11-slim

# Prevent Python from generating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application Code
COPY . .

# --- FIX: Create and Switch to Non-Root User ---
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser
# -----------------------------------------------

# Command to run the worker
CMD ["celery", "-A", "app.core.celery_app.celery_app", "worker", "--loglevel=info"]