.PHONY: help build up down logs shell pull-models clean

# Default compose file (CPU mode)
COMPOSE_FILE ?= docker-compose.cpu.yml

help:
	@echo "LLM Red Team - Docker Commands"
	@echo "=============================="
	@echo ""
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start all services"
	@echo "  make up-gpu       - Start with GPU support"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - View logs"
	@echo "  make shell        - Shell into web container"
	@echo "  make pull-models  - Pull Ollama models"
	@echo "  make clean        - Remove all containers and volumes"
	@echo ""

build:
	docker-compose -f $(COMPOSE_FILE) build

up:
	docker-compose -f docker-compose.cpu.yml up -d
	@echo ""
	@echo "Services started!"
	@echo "Web UI: http://localhost:8000"
	@echo "Ollama: http://localhost:11434"

up-gpu:
	docker-compose -f docker-compose.yml up -d
	@echo ""
	@echo "Services started (GPU mode)!"
	@echo "Web UI: http://localhost:8000"
	@echo "Ollama: http://localhost:11434"

down:
	docker-compose -f docker-compose.cpu.yml down
	docker-compose -f docker-compose.yml down 2>/dev/null || true

logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

shell:
	docker-compose -f $(COMPOSE_FILE) exec web /bin/bash

pull-models:
	@echo "Pulling lightweight models (~950MB total)..."
	docker-compose -f $(COMPOSE_FILE) exec ollama ollama pull smollm:135m
	docker-compose -f $(COMPOSE_FILE) exec ollama ollama pull smollm:360m
	docker-compose -f $(COMPOSE_FILE) exec ollama ollama pull tinyllama
	@echo "All models pulled!"

clean:
	docker-compose -f docker-compose.cpu.yml down -v --remove-orphans
	docker-compose -f docker-compose.yml down -v --remove-orphans 2>/dev/null || true
	docker system prune -f
