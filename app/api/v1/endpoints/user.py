"""
Endpointy API dla użytkowników
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.core.security import get_current_active_user
from app.models.user import User


router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Tworzy nowego użytkownika
    """
    user_service = UserService(db)
    return user_service.create_user(user_data)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera informacje o aktualnie zalogowanym użytkowniku
    """
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera użytkownika po ID
    """
    user_service = UserService(db)
    return user_service.get_user(user_id)


@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera listę użytkowników
    """
    user_service = UserService(db)
    return user_service.get_users(skip=skip, limit=limit)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Aktualizuje dane użytkownika
    """
    user_service = UserService(db)
    return user_service.update_user(user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Usuwa użytkownika
    """
    user_service = UserService(db)
    return user_service.delete_user(user_id)
