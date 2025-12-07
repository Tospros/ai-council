"""
Router główny API v1 - grupuje wszystkie endpointy
"""
from fastapi import APIRouter
from app.api.v1.endpoints import user


api_router = APIRouter()

# Rejestracja routerów
api_router.include_router(
    user.router,
    prefix="/users",
    tags=["users"]
)

# TODO: Dodaj więcej routerów tutaj
# api_router.include_router(
#     council.router,
#     prefix="/council",
#     tags=["council"]
# )
