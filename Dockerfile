FROM python:3.12-slim

WORKDIR /app

# Zainstaluj poetry
RUN pip install poetry

# Skopiuj pliki projektu
COPY pyproject.toml ./
COPY backend.py ./
COPY .env.example ./.env

# Zainstaluj zależności
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

# Uruchom backend
CMD ["python", "backend.py"]
