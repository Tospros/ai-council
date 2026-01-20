from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime


class PromptRequest(BaseModel):
    """Request schema for prompting all models."""
    prompt: str = Field(..., min_length=1, max_length=10000, description="The prompt to send to all models")
    system_prompt: Optional[str] = Field(None, max_length=5000, description="Optional system prompt for context")


class PromptResponse(BaseModel):
    """Response schema containing responses from all models."""
    responses: Dict[str, str] = Field(..., description="Dictionary mapping model names to their responses")


class GradeItem(BaseModel):
    """Individual grade for a model."""
    llama: int = Field(..., ge=1, le=5, description="Rating for llama model (1-5)")
    mistral: int = Field(..., ge=1, le=5, description="Rating for mistral model (1-5)")
    gemma: int = Field(..., ge=1, le=5, description="Rating for gemma model (1-5)")


class RatingRequest(BaseModel):
    """Request schema for submitting ratings."""
    id: str = Field(..., description="The call ID to associate ratings with")
    prompt: Optional[str] = Field(None, description="The original prompt (for storage)")
    responses: Optional[Dict[str, str]] = Field(None, description="The model responses (for storage)")
    grades: GradeItem = Field(..., description="Ratings for each model")


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
    models: List[str] = Field(..., description="Available model names")
    database: str = Field(..., description="Database connection status")
