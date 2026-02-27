"""LLM client — generate text responses via Ollama (local, free)."""

import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Timeout for LLM generation (seconds)
LLM_TIMEOUT = 120.0


async def generate_response(prompt: str) -> str:
    """Send a prompt to Ollama and return the generated text.

    Uses the Ollama REST API at /api/generate.
    Falls back to a polite error message if Ollama is unreachable.
    """
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,   # Lower = more factual / less creative
            "top_p": 0.9,
            "num_predict": 512,   # Max tokens to generate
        },
    }

    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("response", "").strip()
            logger.info(
                "LLM response generated (%d chars, model=%s)",
                len(answer),
                settings.OLLAMA_MODEL,
            )
            return answer

    except httpx.ConnectError:
        logger.error("Cannot connect to Ollama at %s", settings.OLLAMA_BASE_URL)
        return (
            "I'm sorry, the AI service is currently unavailable. "
            "Please try again later or ask to speak with a human agent."
        )
    except httpx.HTTPStatusError as exc:
        logger.error("Ollama returned HTTP %d: %s", exc.response.status_code, exc.response.text[:200])
        return (
            "I encountered an error while generating a response. "
            "Please try again or escalate to a human agent."
        )
    except Exception as exc:
        logger.error("LLM generation failed: %s", exc)
        return (
            "Something went wrong while processing your question. "
            "Please try again shortly."
        )


async def check_ollama_health() -> bool:
    """Check if Ollama is reachable and the configured model is available."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            available = any(settings.OLLAMA_MODEL in m for m in models)
            if not available:
                logger.warning(
                    "Ollama is up but model '%s' not found. Available: %s",
                    settings.OLLAMA_MODEL,
                    models,
                )
            return available
    except Exception:
        return False
