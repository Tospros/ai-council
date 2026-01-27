#!/bin/bash
echo "==================================="
echo "LLM Red Team - Docker Launcher"
echo "==================================="
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker."
    exit 1
fi

# Check for NVIDIA GPU
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected. Using GPU mode."
    COMPOSE_FILE="docker-compose.yml"
else
    echo "No NVIDIA GPU detected. Using CPU-only mode."
    COMPOSE_FILE="docker-compose.cpu.yml"
fi

echo
echo "Starting services..."
echo "This will download models on first run (may take several minutes)."
echo

docker-compose -f $COMPOSE_FILE up --build -d

echo
echo "==================================="
echo "Services starting..."
echo
echo "Web UI: http://localhost:8000"
echo "Ollama: http://localhost:11434"
echo
echo "To view logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "To stop: docker-compose -f $COMPOSE_FILE down"
echo "==================================="
