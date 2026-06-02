from typing import Any

from app.config import get_settings
from app.services.http_clients import get_ollama_client


async def chat_with_ollama(message: str, model: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    selected_model = model or settings.ollama_model
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": selected_model,
        "messages": [{"role": "user", "content": message}],
        "stream": False,
    }

    try:
        client = get_ollama_client()
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "reply": "",
            "error": f"无法连接 Ollama 服务: {exc}",
            "model": selected_model,
            "raw": {},
        }

    reply = data.get("message", {}).get("content", "")
    return {
        "success": True,
        "reply": reply,
        "model": data.get("model", selected_model),
        "raw": data,
    }


async def get_ollama_status() -> dict[str, Any]:
    settings = get_settings()
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        client = get_ollama_client()
        response = await client.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "available": True,
            "provider": "ollama",
            "message": f"已连接，发现 {len(data.get('models', []))} 个模型",
            "models": [item.get("name") for item in data.get("models", [])],
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "provider": "ollama",
            "message": f"Ollama 连接失败: {exc}",
            "models": [],
        }


async def list_ollama_models() -> dict[str, Any]:
    status = await get_ollama_status()
    return {
        "default_model": get_settings().ollama_model,
        "models": status.get("models", []),
    }
