from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime


class PromptRequest(BaseModel):
    """Request schema for prompting all models."""
    prompt: str = Field(..., min_length=1, max_length=10000, description="The prompt to send to attacker models")


class PromptResponse(BaseModel):
    """Response schema containing injection attempts and target responses."""
    session_id: str = Field(..., description="Unique session identifier")
    injection_attempts: Dict[str, str] = Field(..., description="Dictionary mapping attacker model names to their injection attempts")
    target_responses: Dict[str, str] = Field(..., description="Dictionary mapping attacker model names to the target model's responses")


class GradeItem(BaseModel):
    """Individual grades for target responses (keyed by attacker name)."""
    llama: int = Field(..., ge=1, le=5, description="Rating for target's response to llama's attempt (1-5)")
    gemma: int = Field(..., ge=1, le=5, description="Rating for target's response to gemma's attempt (1-5)")


class RatingRequest(BaseModel):
    """Request schema for submitting ratings."""
    id: str = Field(..., description="The session ID to associate ratings with")
    prompt: Optional[str] = Field(None, description="The original prompt (for storage)")
    injection_attempts: Optional[Dict[str, str]] = Field(None, description="The injection attempts (for storage)")
    target_responses: Optional[Dict[str, str]] = Field(None, description="The target responses (for storage)")
    grades: GradeItem = Field(..., description="Ratings for each target response")


class RatingResponse(BaseModel):
    """Response schema for rating submission."""
    success: bool = Field(..., description="Whether the ratings were saved successfully")
    message: str = Field(..., description="Status message")
    saved_count: int = Field(..., description="Number of ratings saved")


class HistoryItem(BaseModel):
    """Schema for a single history item."""
    id: str
    prompt: str
    response: Optional[str]
    rating: int
    llm_name: str
    created_at: datetime


class HistoryResponse(BaseModel):
    """Response schema for history queries."""
    items: List[HistoryItem]
    total: int


class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str = Field(..., description="Health status")
    attacker_models: List[str] = Field(..., description="Available attacker model names")
    target_model: str = Field(..., description="Target model name")
    database: str = Field(..., description="Database connection status")


class ModelsResponse(BaseModel):
    """Response schema for models endpoint."""
    attacker_models: List[str] = Field(..., description="Available attacker model names")
    target_model: str = Field(..., description="Target model name")
