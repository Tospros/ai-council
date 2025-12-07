"""
Konfiguracja sesji bazy danych SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# Tworzenie silnika bazy danych
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Sprawdza połączenie przed użyciem
    pool_size=10,         # Rozmiar puli połączeń
    max_overflow=20       # Maksymalna liczba dodatkowych połączeń
)

# Sesja bazy danych
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Bazowa klasa dla modeli
Base = declarative_base()


def get_db():
    """
    Dependency injection dla sesji bazy danych
    Używane w FastAPI endpoints
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicjalizuje bazę danych - tworzy wszystkie tabele
    """
    Base.metadata.create_all(bind=engine)
