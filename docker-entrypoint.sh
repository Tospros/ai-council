#!/bin/bash
set -e

echo "==================================="
echo "LLM Red Team - Starting Application"
echo "==================================="

# Wait for Ollama to be ready
echo "Waiting for Ollama at ${OLLAMA_HOST}:${OLLAMA_PORT}..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s "http://${OLLAMA_HOST}:${OLLAMA_PORT}/api/tags" > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - Ollama not ready yet..."
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo "Warning: Could not connect to Ollama. Application will start anyway."
fi

# Initialize database
echo "Initializing database..."
cd /app
python -c "from database import init_db; init_db()"
echo "Database initialized!"

# Start Django server directly from frontend directory
echo "Starting Django server on 0.0.0.0:8000..."
cd /app/frontend
exec python manage.py runserver 0.0.0.0:8000 --noreload
