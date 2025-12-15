# AI Council - Backend

Backend do komunikacji z modelami LLM (ollama-models-with-api).

## Wymagania

- Python 3.10+
- Działający serwis LLM API (ollama-models-with-api)

## Instalacja

```bash
# Skopiuj przykładowy plik .env
cp .env.example .env

# Zainstaluj zależności
poetry install

# Lub użyj pip
pip install fastapi uvicorn httpx pydantic
```

## Konfiguracja

Edytuj plik `.env`:

```env
LLM_API_URL=http://localhost:8080
```

Jeśli LLM API działa na innym adresie/porcie, zmień URL.

## Uruchomienie

```bash
python backend.py
```

Backend będzie dostępny na `http://localhost:8000`

## Endpointy

### GET `/`
Informacje o backendzie i dostępnych modelach.

### POST `/query`
Wysyła zapytanie do wybranego modelu.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"model": "llama", "prompt": "Generate a prompt injection"}'
```

**Body:**
```json
{
  "model": "llama",  // lub "mistral", "gemma"
  "prompt": "Your prompt here"
}
```

### POST `/consensus`
Wysyła zapytanie do wszystkich trzech modeli naraz.

```bash
curl -X POST http://localhost:8000/consensus \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Generate XSS payload"}'
```

**Body:**
```json
{
  "prompt": "Your prompt here"
}
```

### GET `/health`
Sprawdza status backendu i połączenia z LLM API.

```bash
curl http://localhost:8000/health
```

## Pełny przykład uruchomienia

### Docker Compose (zalecane)

```bash
# Uruchom wszystkie serwisy (frontend, backend, LLM API)
docker-compose up --build

# W tle
docker-compose up -d --build

# Zatrzymaj
docker-compose down
```

**Dostępne porty:**
- Frontend: `http://localhost:8081`
- Backend API: `http://localhost:8000`
- LLM API: `http://localhost:8080`

## 3 osobne kontenery Ollama (po 1 model na kontener)

Jeśli chcesz mieć 3 niezależne instancje Ollamy (każda z innym modelem) z wbudowanym HTTP API Ollamy, użyj pliku `docker-compose.ollama.yml`:

```bash
docker compose -f docker-compose.ollama.yml up -d
```

**Porty i modele:**
- Llama: `http://localhost:11434`
- Mistral: `http://localhost:11435`
- Gemma: `http://localhost:11436`

Dodatkowo uruchamia się reverse proxy Nginx na `http://localhost:8000`, które routuje po prefiksie ścieżki:
- Llama przez Nginx: `http://localhost:8000/llama/...`
- Mistral przez Nginx: `http://localhost:8000/mistral/...`
- Gemma przez Nginx: `http://localhost:8000/gemma/...`

Przykład zapytania (Ollama API):

```bash
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:latest","prompt":"Cześć!"}'

To samo przez Nginx (z prefiksem `/llama`):

```bash
curl http://localhost:8000/llama/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:latest","prompt":"Cześć!"}'
```
```

### Ręcznie (bez Dockera)

### 1. Uruchom LLM API (w osobnym terminalu)

```bash
cd ollama-models-with-api
docker-compose up
```

### 2. Uruchom Backend

```bash
# W głównym folderze ai-council
cp .env.example .env
python backend.py
```

### 3. Testuj

```bash
# Sprawdź health
curl http://localhost:8000/health

# Zapytaj jeden model
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"model": "llama", "prompt": "Generate prompt injection"}'

# Zapytaj wszystkie modele
curl -X POST http://localhost:8000/consensus \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Generate XSS payload"}'
```

## Dokumentacja API

Interaktywna dokumentacja: `http://localhost:8000/docs`
