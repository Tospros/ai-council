from sqlalchemy import String, Integer, CheckConstraint, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class PromptHistory(Base):
    """Model for storing prompt history with ratings."""
    
    __tablename__ = "prompts_history"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range"),
        {"schema": "main"}
    )
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    llm_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<PromptHistory(id={self.id}, llm_name={self.llm_name}, rating={self.rating})>"
