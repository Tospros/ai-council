# Dockerfile for LLM Red Team Application
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/frontend
ENV DJANGO_SETTINGS_MODULE=settings
ENV OLLAMA_HOST=ollama
ENV OLLAMA_PORT=11434
ENV DEV_MODE=true

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Fix line endings and make entrypoint executable
RUN dos2unix docker-entrypoint.sh && chmod +x docker-entrypoint.sh

# Create directory for database
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/bin/bash", "/app/docker-entrypoint.sh"]
