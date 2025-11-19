# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies (needed for tree-sitter/git)
RUN apt-get update && apt-get install -y git build-essential

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port
EXPOSE 8000

# Command to run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
