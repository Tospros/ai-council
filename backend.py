from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Załaduj zmienne z .env
load_dotenv()

app = FastAPI(title="AI Council Backend")

# Konfiguracja URL do LLM API
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:8080")


class PromptRequest(BaseModel):
    prompt: str
    model: str  # "llama", "mistral", "gemma"


class ConsensusRequest(BaseModel):
    prompt: str


async def query_llm(model: str, prompt: str) -> str:
    """Wysyła zapytanie do wybranego modelu LLM"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{LLM_API_URL}/{model}",
                json={"prompt": prompt}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"LLM API error: {str(e)}")


@app.get("/")
async def root():
    return {
        "message": "AI Council Backend",
        "llm_api_url": LLM_API_URL,
        "available_models": ["llama", "mistral", "gemma"]
    }


@app.post("/query")
async def query_model(request: PromptRequest):
    """Wysyła zapytanie do wybranego modelu"""
    if request.model not in ["llama", "mistral", "gemma"]:
        raise HTTPException(status_code=400, detail="Invalid model. Choose: llama, mistral, or gemma")
    
    response = await query_llm(request.model, request.prompt)
    return {
        "model": request.model,
        "prompt": request.prompt,
        "response": response
    }


@app.post("/consensus")
async def get_consensus(request: ConsensusRequest):
    """Wysyła zapytanie do wszystkich trzech modeli i zwraca ich odpowiedzi"""
    results = {}
    
    for model in ["llama", "mistral", "gemma"]:
        try:
            response = await query_llm(model, request.prompt)
            results[model] = response
        except Exception as e:
            results[model] = f"Error: {str(e)}"
    
    return {
        "prompt": request.prompt,
        "responses": results
    }


@app.get("/health")
async def health_check():
    """Sprawdza czy backend i LLM API działają"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LLM_API_URL}/")
            llm_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        llm_status = "unreachable"
    
    return {
        "backend": "healthy",
        "llm_api": llm_status,
        "llm_api_url": LLM_API_URL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
