FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry

COPY ../pyproject.toml ./
COPY ../backend.py ./
COPY .env.example ./.env

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

CMD ["python", "backend.py"]
