# ===== Multi-stage Dockerfile dla AI Council ===== 

# Stage 1: Builder
FROM python:3.11-slim as builder

LABEL maintainer="AI Council Team"
LABEL description="AI Council - Multi-LLM Collaborative Platform"

# Zmienne środowiskowe dla Pythona
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Tworzenie katalogu roboczego
WORKDIR /build

# Kopiowanie requirements i instalacja zależności
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt


# Stage 2: Runtime
FROM python:3.11-slim

# Zmienne środowiskowe
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    APP_HOME=/app

# Instalacja runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tworzenie użytkownika non-root
RUN useradd -m -u 1000 appuser && \
    mkdir -p $APP_HOME && \
    chown -R appuser:appuser $APP_HOME

# Kopiowanie zainstalowanych pakietów z buildera
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Przełączenie na użytkownika non-root
USER appuser

# Ustawienie katalogu roboczego
WORKDIR $APP_HOME

# Kopiowanie kodu aplikacji
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./front ./front
COPY --chown=appuser:appuser .env* ./

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Uruchomienie aplikacji
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
