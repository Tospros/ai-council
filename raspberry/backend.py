from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
import httpx
import asyncio
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL_1 = os.getenv("API_URL_1")
API_URL_2 = os.getenv("API_URL_2")
API_URL_3 = os.getenv("API_URL_3")
MODEL_NAME_1 = os.getenv("MODEL_NAME_1")
MODEL_NAME_2 = os.getenv("MODEL_NAME_2")
MODEL_NAME_3 = os.getenv("MODEL_NAME_3")
TIMEOUT = int(os.getenv("TIMEOUT"))


class PromptRequest(BaseModel):
    prompt: str


class ModelResponse(BaseModel):
    responses: dict[str, str]


async def query_endpoint(client: httpx.AsyncClient, url: str, model_name: str, prompt: str) -> tuple[str, str]:
    try:
        response = await client.post(
            url,
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        return model_name, data.get("response", str(data))
    except httpx.TimeoutException:
        return model_name, f"Timeout po {TIMEOUT}s"
    except Exception as e:
        return model_name, f"Błąd: {str(e)}"


@app.post("/api/prompt-all-models")
async def prompt_all_models(request: PromptRequest):
    endpoints = [
        (API_URL_1, MODEL_NAME_1),
        (API_URL_2, MODEL_NAME_2),
        (API_URL_3, MODEL_NAME_3)
    ]

    async with httpx.AsyncClient() as client:
        tasks = [query_endpoint(client, url, model, request.prompt) for url, model in endpoints]
        results = await asyncio.gather(*tasks)

    responses = {model: response for model, response in results}
    return responses


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
