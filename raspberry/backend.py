from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from databases import Database
from datetime import datetime
import uvicorn
import httpx
import asyncio
import os
import json
import time

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://council_user:pass123@postgres:5432/ai_council")
database = Database(DATABASE_URL)

# Ollama configuration
API_URL = os.getenv("API_URL", "http://192.168.1.20:11434/api/generate")
MODEL_NAMES = os.getenv("MODEL_NAMES", "tinyllama,dolphin-mistral,gemma2:2b").split(",")
TIMEOUT = int(os.getenv("TIMEOUT", "120"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to database
    await database.connect()
    yield
    # Shutdown: disconnect from database
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str
    session_id: str | None = None


class RatingRequest(BaseModel):
    id: str  # session_id
    grades: dict[str, int]


class HistoryResponse(BaseModel):
    sessions: list[dict]


async def query_model(client: httpx.AsyncClient, model_name: str, prompt: str) -> tuple[str, str, int]:
    """Query a single model and return (model_name, response, time_ms)"""
    start_time = time.time()
    try:
        response = await client.post(
            API_URL,
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        text = response.text.strip()
        lines = [line for line in text.split('\n') if line.strip()]
        
        if not lines:
            return model_name, "Empty response", 0
        
        data = json.loads(lines[-1])
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        return model_name, data.get("response", str(data)), elapsed_ms
    except httpx.TimeoutException:
        return model_name, f"Timeout after {TIMEOUT}s", 0
    except Exception as e:
        return model_name, f"Error: {str(e)}", 0


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/models")
async def get_models():
    """Return list of available models"""
    return {"models": MODEL_NAMES}


@app.post("/api/prompt-all-models")
async def prompt_all_models(request: PromptRequest):
    """Send prompt to all models and store results in database"""
    
    # Generate session ID if not provided
    session_id = request.session_id
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
    
    # Create session in database
    await database.execute(
        "INSERT INTO main.sessions (id) VALUES (:id)",
        {"id": session_id}
    )
    
    # Store the prompt
    await database.execute(
        "INSERT INTO main.prompts (session_id, prompt_text) VALUES (:session_id, :prompt_text)",
        {"session_id": session_id, "prompt_text": request.prompt}
    )
    
    # Query only tinyllama, use dummy responses for others (for testing)
    async with httpx.AsyncClient() as client:
        tinyllama_result = await query_model(client, MODEL_NAMES[0], request.prompt)
    
    responses = {}
    
    # Process tinyllama response
    model_name, response_text, response_time_ms = tinyllama_result
    responses[model_name] = response_text
    await database.execute(
        """INSERT INTO main.responses (session_id, model_name, response_text, response_time_ms) 
           VALUES (:session_id, :model_name, :response_text, :response_time_ms)""",
        {
            "session_id": session_id,
            "model_name": model_name,
            "response_text": response_text,
            "response_time_ms": response_time_ms
        }
    )
    
    # Add dummy responses for other models
    for model in MODEL_NAMES[1:]:
        dummy_response = f"[DUMMY] This is a placeholder response from {model}. Prompt: {request.prompt[:50]}..."
        responses[model] = dummy_response
        
        await database.execute(
            """INSERT INTO main.responses (session_id, model_name, response_text, response_time_ms) 
               VALUES (:session_id, :model_name, :response_text, :response_time_ms)""",
            {
                "session_id": session_id,
                "model_name": model,
                "response_text": dummy_response,
                "response_time_ms": 0
            }
        )
    
    return {"session_id": session_id, **responses}


@app.post("/api/answers")
async def submit_ratings(request: RatingRequest):
    """Store user ratings for model responses"""
    
    # Verify session exists
    session = await database.fetch_one(
        "SELECT id FROM main.sessions WHERE id = :id",
        {"id": request.id}
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store ratings (upsert)
    for model_name, rating in request.grades.items():
        if not (1 <= rating <= 5):
            raise HTTPException(status_code=400, detail=f"Rating must be between 1 and 5, got {rating}")
        
        await database.execute(
            """INSERT INTO main.ratings (session_id, model_name, rating) 
               VALUES (:session_id, :model_name, :rating)
               ON CONFLICT (session_id, model_name) 
               DO UPDATE SET rating = :rating, created_at = NOW()""",
            {
                "session_id": request.id,
                "model_name": model_name,
                "rating": rating
            }
        )
    
    return {"status": "ok", "session_id": request.id}


@app.get("/api/history")
async def get_history(limit: int = 50):
    """Get history of prompts, responses, and ratings"""
    
    sessions = await database.fetch_all(
        """SELECT s.id, s.created_at, p.prompt_text
           FROM main.sessions s
           LEFT JOIN main.prompts p ON s.id = p.session_id
           ORDER BY s.created_at DESC
           LIMIT :limit""",
        {"limit": limit}
    )
    
    result = []
    for session in sessions:
        session_id = str(session["id"])
        
        # Get responses for this session
        responses = await database.fetch_all(
            """SELECT model_name, response_text, response_time_ms 
               FROM main.responses WHERE session_id = :session_id""",
            {"session_id": session_id}
        )
        
        # Get ratings for this session
        ratings = await database.fetch_all(
            """SELECT model_name, rating 
               FROM main.ratings WHERE session_id = :session_id""",
            {"session_id": session_id}
        )
        
        result.append({
            "session_id": session_id,
            "created_at": session["created_at"].isoformat() if session["created_at"] else None,
            "prompt": session["prompt_text"],
            "responses": {r["model_name"]: {
                "text": r["response_text"],
                "time_ms": r["response_time_ms"]
            } for r in responses},
            "ratings": {r["model_name"]: r["rating"] for r in ratings}
        })
    
    return {"sessions": result}


@app.get("/api/stats")
async def get_stats():
    """Get aggregate statistics"""
    
    total_sessions = await database.fetch_one(
        "SELECT COUNT(*) as count FROM main.sessions"
    )
    
    total_ratings = await database.fetch_one(
        "SELECT COUNT(*) as count FROM main.ratings"
    )
    
    avg_ratings = await database.fetch_all(
        """SELECT model_name, AVG(rating) as avg_rating, COUNT(*) as count
           FROM main.ratings
           GROUP BY model_name"""
    )
    
    return {
        "total_sessions": total_sessions["count"] if total_sessions else 0,
        "total_ratings": total_ratings["count"] if total_ratings else 0,
        "model_stats": {
            r["model_name"]: {
                "avg_rating": round(float(r["avg_rating"]), 2),
                "count": r["count"]
            } for r in avg_ratings
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
