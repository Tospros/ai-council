"""
Serwis użytkowników - logika biznesowa
"""
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import verify_password


class UserService:
    """
    Serwis obsługujący logikę biznesową dla użytkowników
    """
    
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
    
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Tworzy nowego użytkownika z walidacją
        """
        # Sprawdzenie czy email już istnieje
        if self.repository.exists(email=user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Sprawdzenie czy username już istnieje
        if self.repository.exists(username=user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Tworzenie użytkownika
        user = self.repository.create(user_data)
        
        return UserResponse.model_validate(user)
    
    def get_user(self, user_id: int) -> UserResponse:
        """
        Pobiera użytkownika po ID
        """
        user = self.repository.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.model_validate(user)
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """
        Pobiera listę użytkowników
        """
        users = self.repository.get_all(skip=skip, limit=limit)
        return [UserResponse.model_validate(user) for user in users]
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """
        Aktualizuje dane użytkownika
        """
        # Sprawdzenie czy użytkownik istnieje
        existing_user = self.repository.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Sprawdzenie czy nowy email nie jest już zajęty
        if user_data.email and user_data.email != existing_user.email:
            if self.repository.exists(email=user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Sprawdzenie czy nowy username nie jest już zajęty
        if user_data.username and user_data.username != existing_user.username:
            if self.repository.exists(username=user_data.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Aktualizacja użytkownika
        updated_user = self.repository.update(user_id, user_data)
        
        return UserResponse.model_validate(updated_user)
    
    def delete_user(self, user_id: int) -> dict:
        """
        Usuwa użytkownika (soft delete)
        """
        success = self.repository.delete(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deleted successfully"}
    
    def authenticate(self, identifier: str, password: str):
        """
        Autentykuje użytkownika po email/username i haśle
        """
        user = self.repository.get_by_email_or_username(identifier)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
