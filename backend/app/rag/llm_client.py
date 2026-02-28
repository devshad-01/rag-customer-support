"""LLM client — generate text via Ollama (local) or Google Gemini (online)."""

import logging
import asyncio
import httpx
from google import genai

from app.config import settings

logger = logging.getLogger(__name__)

# Timeout for LLM generation (seconds)
LLM_TIMEOUT = 120.0

# ── Gemini client (initialised lazily) ────────────────────────
_gemini_client: genai.Client | None = None


def _get_gemini_client() -> genai.Client:
    """Return a cached Gemini client, creating one on first call."""
    global _gemini_client
    if _gemini_client is None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set in .env")
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini client initialised (model=%s)", settings.GEMINI_MODEL)
    return _gemini_client


# ── Provider-specific generators ──────────────────────────────

async def _generate_ollama(prompt: str) -> str:
    """Generate a response using local Ollama server."""
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": 512,
        },
    }

    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("response", "").strip()
        logger.info(
            "Ollama response generated (%d chars, model=%s)",
            len(answer),
            settings.OLLAMA_MODEL,
        )
        return answer


async def _generate_gemini(prompt: str) -> str:
    """Generate a response using Google Gemini API."""
    client = _get_gemini_client()
    # Run blocking SDK call in a thread to avoid blocking the event loop
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.9,
            max_output_tokens=512,
        ),
    )
    answer = response.text.strip() if response.text else ""
    logger.info(
        "Gemini response generated (%d chars, model=%s)",
        len(answer),
        settings.GEMINI_MODEL,
    )
    return answer


# ── Public API ────────────────────────────────────────────────

async def generate_response(prompt: str) -> str:
    """Send a prompt to the configured LLM provider and return text.

    Provider is determined by settings.LLM_PROVIDER ('ollama' or 'gemini').
    Falls back to a polite error message on failure.
    """
    provider = settings.LLM_PROVIDER.lower()
    try:
        if provider == "gemini":
            return await _generate_gemini(prompt)
        else:
            return await _generate_ollama(prompt)

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
        logger.error("LLM generation failed (%s): %s", provider, exc)
        return (
            "Something went wrong while processing your question. "
            "Please try again shortly."
        )


async def check_llm_health() -> dict:
    """Check if the configured LLM provider is reachable.

    Returns a dict with 'provider', 'healthy', and 'model' keys.
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        try:
            client = _get_gemini_client()
            # Quick test — list models to confirm API key works
            models = list(client.models.list())
            available = any(settings.GEMINI_MODEL in m.name for m in models)
            if not available:
                logger.warning(
                    "Gemini API key works but model '%s' not found.",
                    settings.GEMINI_MODEL,
                )
            return {"provider": "gemini", "healthy": True, "model": settings.GEMINI_MODEL}
        except Exception as exc:
            logger.error("Gemini health check failed: %s", exc)
            return {"provider": "gemini", "healthy": False, "model": settings.GEMINI_MODEL}
    else:
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
                return {"provider": "ollama", "healthy": available, "model": settings.OLLAMA_MODEL}
        except Exception:
            return {"provider": "ollama", "healthy": False, "model": settings.OLLAMA_MODEL}
