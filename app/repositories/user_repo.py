"""
Repository dla operacji na użytkownikach w bazie danych
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserRepository:
    """
    Repository obsługujące zapytania do bazy danych dla użytkowników
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Pobiera użytkownika po ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Pobiera użytkownika po adresie email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Pobiera użytkownika po nazwie użytkownika"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email_or_username(self, identifier: str) -> Optional[User]:
        """Pobiera użytkownika po email lub username"""
        return self.db.query(User).filter(
            or_(User.email == identifier, User.username == identifier)
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Pobiera listę użytkowników z paginacją"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def create(self, user_data: UserCreate) -> User:
        """Tworzy nowego użytkownika"""
        hashed_password = get_password_hash(user_data.password)
        
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Aktualizuje dane użytkownika"""
        db_user = self.get_by_id(user_id)
        
        if not db_user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        # Jeśli aktualizujemy hasło, hashujemy je
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def delete(self, user_id: int) -> bool:
        """Usuwa użytkownika (soft delete - ustawia is_active=False)"""
        db_user = self.get_by_id(user_id)
        
        if not db_user:
            return False
        
        db_user.is_active = False
        self.db.commit()
        
        return True
    
    def hard_delete(self, user_id: int) -> bool:
        """Usuwa użytkownika permanentnie z bazy danych"""
        db_user = self.get_by_id(user_id)
        
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        
        return True
    
    def exists(self, email: str = None, username: str = None) -> bool:
        """Sprawdza czy użytkownik z danym email lub username istnieje"""
        query = self.db.query(User)
        
        if email:
            query = query.filter(User.email == email)
        
        if username:
            query = query.filter(User.username == username)
        
        return query.first() is not None
