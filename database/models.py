"""
SQLAlchemy models for LLM Red Team application.
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class JailbreakSession(Base):
    """Represents a single jailbreak testing session."""
    __tablename__ = 'jailbreak_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    attempts = relationship("JailbreakAttempt", back_populates="session", cascade="all, delete-orphan")


class JailbreakAttempt(Base):
    """Represents a single jailbreak attempt by one of the attacker LLMs."""
    __tablename__ = 'jailbreak_attempts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('jailbreak_sessions.id'), nullable=False)

    # Attacker LLM info
    attacker_model = Column(String(100), nullable=False)  # qwen2.5:1.5b, deepseek-r1:1.5b, gemma3:1b
    attacker_prompt = Column(Text, nullable=False)  # Generated jailbreak prompt

    # Target LLM response
    target_model = Column(String(100), default="gemma3:1b")
    target_response = Column(Text, nullable=True)

    # Rating
    user_rating = Column(Float, nullable=True)  # 1-5 scale
    rating_comment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    rated_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("JailbreakSession", back_populates="attempts")


class ModelStats(Base):
    """Statistics for each attacker model."""
    __tablename__ = 'model_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), unique=True, nullable=False)
    total_attempts = Column(Integer, default=0)
    total_ratings = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database configuration
import os
DB_PATH = os.environ.get('DB_PATH', './llm_redteam.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
