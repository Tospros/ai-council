from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from app.api.schemas import (
    PromptRequest,
    PromptResponse,
    RatingRequest,
    RatingResponse,
    HealthResponse,
    HistoryResponse,
    HistoryItem,
)
from app.database import get_db
from app.database.repository import PromptHistoryRepository
from app.llm.service import get_llm_service, LLMService
from app.llm.graph import create_council_graph

router = APIRouter()


def get_repository(db: AsyncSession = Depends(get_db)) -> PromptHistoryRepository:
    """Dependency for getting the repository."""
    return PromptHistoryRepository(db)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Health check endpoint."""
    db_status = "connected"
    try:
        # Simple query to check database connection
        await db.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy",
        models=llm_service.available_models,
        database=db_status
    )


@router.post("/api/prompt-all-models", response_model=Dict[str, str])
async def prompt_all_models(
    request: PromptRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Send a prompt to all LLM models and get their responses.
    
    Uses LangChain to communicate with Ollama models in parallel.
    """
    try:
        # Use the parallel council graph for efficient querying
        council = create_council_graph(parallel=True)
        responses = await council.run(
            prompt=request.prompt,
            system_prompt=request.system_prompt
        )
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying models: {str(e)}")


@router.post("/api/answers", response_model=RatingResponse)
async def submit_ratings(
    request: RatingRequest,
    repo: PromptHistoryRepository = Depends(get_repository)
):
    """
    Submit ratings for model responses.
    
    Stores the prompt, responses, and ratings in the database.
    """
    try:
        records_to_create = []
        grades_dict = request.grades.model_dump()
        
        for model_name, rating in grades_dict.items():
            response_text = None
            if request.responses:
                response_text = request.responses.get(model_name)
            
            records_to_create.append({
                "id": f"{request.id}_{model_name}",
                "prompt": request.prompt or "",
                "response": response_text,
                "rating": rating,
                "llm_name": model_name,
            })
        
        await repo.bulk_create(records_to_create)
        
        return RatingResponse(
            success=True,
            message="Ratings saved successfully",
            saved_count=len(records_to_create)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving ratings: {str(e)}")


@router.get("/api/history", response_model=HistoryResponse)
async def get_history(
    limit: int = 100,
    offset: int = 0,
    llm_name: str = None,
    repo: PromptHistoryRepository = Depends(get_repository)
):
    """
    Get prompt history with ratings.
    
    Optionally filter by LLM name.
    """
    try:
        if llm_name:
            items = await repo.get_by_llm_name(llm_name, limit)
        else:
            items = await repo.get_all(limit, offset)
        
        return HistoryResponse(
            items=[
                HistoryItem(
                    id=item.id,
                    prompt=item.prompt,
                    response=item.response,
                    rating=item.rating,
                    llm_name=item.llm_name,
                    created_at=item.created_at
                )
                for item in items
            ],
            total=len(items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Council Backend",
        "version": "0.2.0",
        "description": "Backend for AI Council - LLM communication via LangChain",
        "endpoints": {
            "health": "/health",
            "prompt_all": "/api/prompt-all-models",
            "submit_ratings": "/api/answers",
            "history": "/api/history"
        }
    }
