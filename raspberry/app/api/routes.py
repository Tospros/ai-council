from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api.schemas import (
    PromptRequest,
    PromptResponse,
    RatingRequest,
    RatingResponse,
    HealthResponse,
    HistoryResponse,
    HistoryItem,
    ModelsResponse,
)
from app.database import get_db
from app.database.repository import PromptHistoryRepository
from app.llm.service import get_llm_service, LLMService
from app.llm.graph import create_injection_graph

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
        await db.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy",
        attacker_models=llm_service.available_attacker_models,
        target_model=llm_service.target_model_name,
        database=db_status
    )


@router.get("/api/models", response_model=ModelsResponse)
async def get_models(
    llm_service: LLMService = Depends(get_llm_service)
):
    """Get available attacker models and target model."""
    return ModelsResponse(
        attacker_models=llm_service.available_attacker_models,
        target_model=llm_service.target_model_name
    )


@router.post("/api/prompt-all-models", response_model=PromptResponse)
async def prompt_all_models(
    request: PromptRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Run the injection testing workflow:
    1. Send prompt to all attacker models to generate injection attempts
    2. Send each injection attempt to the target model
    3. Return both injection attempts and target responses
    """
    try:
        session_id = str(uuid.uuid4())

        # Use the injection graph for the workflow
        injection_graph = create_injection_graph(llm_service)
        result = await injection_graph.run(prompt=request.prompt)

        return PromptResponse(
            session_id=session_id,
            injection_attempts=result["injection_attempts"],
            target_responses=result["target_responses"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running injection workflow: {str(e)}")


@router.post("/api/answers", response_model=RatingResponse)
async def submit_ratings(
    request: RatingRequest,
    repo: PromptHistoryRepository = Depends(get_repository)
):
    """
    Submit ratings for target model responses.

    Stores the prompt, injection attempts, target responses, and ratings in the database.
    """
    try:
        records_to_create = []
        grades_dict = request.grades.model_dump()

        for attacker_name, rating in grades_dict.items():
            # Get the injection attempt and target response for this attacker
            injection_attempt = None
            target_response = None
            if request.injection_attempts:
                injection_attempt = request.injection_attempts.get(attacker_name)
            if request.target_responses:
                target_response = request.target_responses.get(attacker_name)

            # Store injection attempt and target response together
            combined_response = ""
            if injection_attempt:
                combined_response += f"[INJECTION ATTEMPT]\n{injection_attempt}\n\n"
            if target_response:
                combined_response += f"[TARGET RESPONSE]\n{target_response}"

            records_to_create.append({
                "id": f"{request.id}_{attacker_name}",
                "prompt": request.prompt or "",
                "response": combined_response or None,
                "rating": rating,
                "llm_name": f"target_via_{attacker_name}",
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
        "name": "AI Council Backend - Injection Testing",
        "version": "0.3.0",
        "description": "Backend for prompt injection testing platform",
        "endpoints": {
            "health": "/health",
            "models": "/api/models",
            "prompt_all": "/api/prompt-all-models",
            "submit_ratings": "/api/answers",
            "history": "/api/history"
        }
    }
