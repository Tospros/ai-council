"""
Główny punkt wejścia aplikacji FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import init_db


# Inicjalizacja aplikacji FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Council - Multi-LLM Collaborative Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Event startup
@app.on_event("startup")
async def startup_event():
    """
    Wykonywane przy starcie aplikacji
    """
    print("🚀 Starting AI Council application...")
    init_db()
    print("✅ Database initialized")


# Event shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """
    Wykonywane przy zamykaniu aplikacji
    """
    print("👋 Shutting down AI Council application...")


# Rejestracja routerów API
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Serwowanie plików statycznych (frontend)
if os.path.exists("front"):
    app.mount("/static", StaticFiles(directory="front"), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        """Serwuje główną stronę frontendu"""
        with open("front/index.html", "r", encoding="utf-8") as f:
            return f.read()


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Sprawdza stan aplikacji
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Root endpoint (jeśli nie ma frontendu)
@app.get("/api", tags=["root"])
async def root():
    """
    Root endpoint API
    """
    return {
        "message": "Welcome to AI Council API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
