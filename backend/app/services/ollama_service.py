import asyncio
from typing import Any

from app.config import get_settings
from app.services.http_clients import get_ollama_client


def _resolve_active_model(default_model: str, running_models: list[str]) -> str | None:
    if default_model in running_models:
        return default_model
    return running_models[0] if running_models else None


async def chat_with_ollama(message: str, model: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    selected_model = model or settings.ollama_model
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": selected_model,
        "messages": [{"role": "user", "content": message}],
        "stream": False,
        "keep_alive": settings.ollama_keep_alive,
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
    base_url = settings.ollama_base_url.rstrip("/")
    tags_url = f"{base_url}/api/tags"
    ps_url = f"{base_url}/api/ps"
    try:
        client = get_ollama_client()
        tags_response, ps_response = await asyncio.gather(
            client.get(tags_url, timeout=10),
            client.get(ps_url, timeout=10),
        )
        tags_response.raise_for_status()
        ps_response.raise_for_status()
        tags_data = tags_response.json()
        ps_data = ps_response.json()
        installed_models = [item.get("name") for item in tags_data.get("models", []) if item.get("name")]
        running_models = [item.get("name") for item in ps_data.get("models", []) if item.get("name")]
        active_model = _resolve_active_model(settings.ollama_model, running_models)
        message = (
            f"已连接，运行中 {len(running_models)} 个模型，已安装 {len(installed_models)} 个模型"
            if running_models
            else f"已连接，当前没有运行中的模型，已安装 {len(installed_models)} 个模型"
        )
        return {
            "available": True,
            "provider": "ollama",
            "message": message,
            "models": installed_models,
            "running_models": running_models,
            "active_model": active_model,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "provider": "ollama",
            "message": f"Ollama 连接失败: {exc}",
            "models": [],
            "running_models": [],
            "active_model": None,
        }


async def list_ollama_models() -> dict[str, Any]:
    status = await get_ollama_status()
    return {
        "default_model": get_settings().ollama_model,
        "models": status.get("models", []),
        "running_models": status.get("running_models", []),
        "active_model": status.get("active_model"),
    }


async def start_ollama_model(model: str) -> dict[str, Any]:
    settings = get_settings()
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "keep_alive": settings.ollama_keep_alive,
    }

    try:
        client = get_ollama_client()
        response = await client.post(url, json=payload, timeout=settings.ollama_model_start_timeout)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "message": f"启动模型失败: {exc}",
            "model": model,
        }

    status = await get_ollama_status()
    return {
        "success": True,
        "message": f"模型 {model} 已启动",
        "model": model,
        "status": status,
    }
