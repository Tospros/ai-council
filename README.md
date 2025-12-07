# AI Council

Multi-LLM Collaborative Platform - aplikacja wykorzystująca trzy różne modele AI (GPT-4, Claude, Gemini) do analizy pytań użytkownika oraz arbitra do syntetyzowania finalnej odpowiedzi.

## 🏗️ Architektura

### Backend (FastAPI + SQLAlchemy)
```
app/
├── main.py                 # Punkt wejścia aplikacji
├── core/
│   ├── config.py          # Konfiguracja (ENV variables)
│   └── security.py        # JWT, hashowanie, autoryzacja
├── models/
│   └── user.py            # Modele SQLAlchemy
├── schemas/
│   └── user.py            # Pydantic Schemas
├── services/
│   └── user_service.py    # Logika biznesowa
├── repositories/
│   └── user_repo.py       # Warstwa dostępu do danych
├── api/
│   └── v1/
│       ├── router.py      # Router główny
│       └── endpoints/
│           └── user.py    # Endpointy użytkowników
└── db/
    └── session.py         # Konfiguracja bazy danych
```

### Frontend (Vanilla JavaScript)
```
front/
├── index.html             # Struktura HTML
├── style.css              # Stylowanie
└── app.js                 # Logika aplikacji
```

## 🚀 Uruchomienie z Docker

### Wymagania
- Docker
- Docker Compose

### Krok 1: Sklonuj repozytorium
```bash
git clone https://github.com/Tospros/ai-council.git
cd ai-council
```

### Krok 2: Skonfiguruj zmienne środowiskowe
```bash
cp .env.example .env
# Edytuj .env i dodaj swoje klucze API dla LLM
```

### Krok 3: Uruchom aplikację
```bash
# Uruchom całą aplikację (backend + database)
docker-compose up -d

# Lub z pgAdmin (narzędzie do zarządzania bazą)
docker-compose --profile tools up -d
```

### Krok 4: Dostęp do aplikacji
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **pgAdmin** (jeśli włączony): http://localhost:5050

### Zatrzymanie aplikacji
```bash
docker-compose down

# Zatrzymanie z usunięciem volumes (baza danych)
docker-compose down -v
```

## 🛠️ Rozwój lokalny (bez Docker)

### Wymagania
- Python 3.11+
- PostgreSQL 14+

### Instalacja

1. **Utwórz wirtualne środowisko**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. **Zainstaluj zależności**
```bash
pip install -r requirements.txt
```

3. **Skonfiguruj bazę danych**
```bash
# Utwórz bazę PostgreSQL
createdb ai_council

# Ustaw DATABASE_URL w .env
DATABASE_URL=postgresql://user:password@localhost:5432/ai_council
```

4. **Uruchom aplikację**
```bash
uvicorn app.main:app --reload
```

## 📝 Dokumentacja API

### Endpointy użytkowników

**POST** `/api/v1/users/` - Rejestracja użytkownika
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "secure_password",
  "full_name": "John Doe"
}
```

**GET** `/api/v1/users/me` - Pobranie danych zalogowanego użytkownika

**GET** `/api/v1/users/{user_id}` - Pobranie użytkownika po ID

**PUT** `/api/v1/users/{user_id}` - Aktualizacja użytkownika

**DELETE** `/api/v1/users/{user_id}` - Usunięcie użytkownika

## 🔑 Konfiguracja API Keys

W pliku `.env` ustaw klucze API dla modeli LLM:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

## 🧪 Testowanie

```bash
pytest
```

## 📦 Budowanie Docker Image

```bash
# Build
docker build -t ai-council:latest .

# Run
docker run -p 8000:8000 --env-file .env ai-council:latest
```

## 🔐 Bezpieczeństwo

- Hasła są hashowane z użyciem bcrypt
- JWT do autoryzacji
- CORS skonfigurowany
- Walidacja danych z Pydantic
- Non-root user w kontenerze Docker

## 📄 Licencja

MIT License

## 👥 Autorzy

AI Council Team
