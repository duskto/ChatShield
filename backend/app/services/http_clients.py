import httpx

from app.config import get_settings


_moderation_client: httpx.AsyncClient | None = None
_ollama_client: httpx.AsyncClient | None = None


def get_moderation_client() -> httpx.AsyncClient:
    global _moderation_client
    if _moderation_client is None:
        _moderation_client = httpx.AsyncClient(timeout=30)
    return _moderation_client


def get_ollama_client() -> httpx.AsyncClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = httpx.AsyncClient(timeout=get_settings().ollama_timeout)
    return _ollama_client


async def close_http_clients() -> None:
    global _moderation_client, _ollama_client

    if _moderation_client is not None:
        await _moderation_client.aclose()
        _moderation_client = None

    if _ollama_client is not None:
        await _ollama_client.aclose()
        _ollama_client = None
