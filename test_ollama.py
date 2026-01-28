#!/usr/bin/env python
import asyncio
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'httpx'])
    import httpx


async def test_ollama_connection(host: str = "localhost", port: int = 11434):
    base_url = f"http://{host}:{port}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"\nTesting connection to {base_url}...")
        try:
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                print("Connected successfully!")
                data = response.json()
                models = data.get("models", [])
                print(f"\nAvailable models ({len(models)}):")
                for model in models:
                    name = model.get("name", "unknown")
                    size = model.get("size", 0) / (1024**3)  # Convert to GB
                    print(f"  - {name} ({size:.2f} GB)")
                return models
            else:
                print(f"Error: Status {response.status_code}")
                return []
        except httpx.ConnectError:
            print(f"Could not connect to Ollama at {base_url}")
            print("Make sure Ollama is running: ollama serve")
            return []


async def test_model_generation(
    model: str,
    prompt: str,
    host: str = "localhost",
    port: int = 11434
):
    base_url = f"http://{host}:{port}"

    print(f"\nTesting generation with {model}...")
    print(f"Prompt: {prompt[:50]}...")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": 2048,
                        "temperature": 0.7
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                text = data.get("response", "")
                print(f"\nResponse:\n{text[:500]}...")
                return text
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None

        except httpx.ReadTimeout:
            print("Request timed out. Model may be loading or slow.")
            return None


async def main():
    print("=" * 60)
    print("Ollama Connectivity Test")
    print("=" * 60)

    # Test local Ollama
    models = await test_ollama_connection()

    if not models:
        print("\nNo models found. Install required models with:")
        print("  ollama pull qwen2.5:1.5b")
        print("  ollama pull deepseek-r1:1.5b")
        print("  ollama pull gemma3:1b")
        return

    # Required models
    required = ["qwen2.5:1.5b", "deepseek-r1:1.5b", "gemma3:1b"]
    available_names = [m.get("name", "").split(":")[0] + ":" +
                      m.get("name", "").split(":")[-1]
                      for m in models]

    print("\n" + "=" * 60)
    print("Required Models Check")
    print("=" * 60)

    for model in required:
        found = any(model.lower() in name.lower() for name in available_names)
        status = "OK" if found else "MISSING"
        print(f"  {model}: {status}")

    if models:
        test_model = models[0].get("name", "")
        if test_model:
            print("\n" + "=" * 60)
            print("Generation Test")
            print("=" * 60)
            await test_model_generation(
                test_model,
                "Write a haiku about programming."
            )


if __name__ == "__main__":
    asyncio.run(main())
