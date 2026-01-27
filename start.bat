@echo off
echo ===================================
echo LLM Red Team - Docker Launcher
echo ===================================
echo.

REM Check if Docker is running
docker info > nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

REM Check for NVIDIA GPU
nvidia-smi > nul 2>&1
if errorlevel 1 (
    echo No NVIDIA GPU detected. Using CPU-only mode.
    echo.
    set COMPOSE_FILE=docker-compose.cpu.yml
) else (
    echo NVIDIA GPU detected. Using GPU mode.
    echo.
    set COMPOSE_FILE=docker-compose.yml
)

echo Starting services...
echo This will download models on first run (may take several minutes).
echo.

docker-compose -f %COMPOSE_FILE% up --build -d

echo.
echo ===================================
echo Services starting...
echo.
echo Web UI: http://localhost:8000
echo Ollama: http://localhost:11434
echo.
echo To view logs: docker-compose -f %COMPOSE_FILE% logs -f
echo To stop: docker-compose -f %COMPOSE_FILE% down
echo ===================================

pause
