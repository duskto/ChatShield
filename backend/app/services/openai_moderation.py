from typing import Any

from app.config import get_settings
from app.services.http_clients import get_moderation_client


OPENAI_CATEGORY_MAPPING = {
    "violence": "violence",
    "violence/graphic": "violence",
    "sexual": "sexual",
    "sexual/minors": "sexual",
    "hate": "hate",
    "hate/threatening": "hate",
    "self-harm": "self_harm",
    "self-harm/instructions": "self_harm",
    "self-harm/intent": "self_harm",
    "illicit": "illegal",
    "illicit/violent": "illegal",
}


def _map_categories(categories: dict[str, bool]) -> list[str]:
    result = []
    for key, value in categories.items():
        if value and key in OPENAI_CATEGORY_MAPPING:
            result.append(OPENAI_CATEGORY_MAPPING[key])
    return sorted(set(result))


async def moderate_with_openai(text: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY 未配置")

    url = f"{settings.openai_base_url.rstrip('/')}/moderations"
    payload = {"model": settings.openai_moderation_model, "input": text}
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    client = get_moderation_client()
    response = await client.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    result = data["results"][0]
    risk_types = _map_categories(result.get("categories", {}))
    flagged = result.get("flagged", False)
    return {
        "safe": not flagged,
        "risk_level": "high" if flagged else "low",
        "risk_types": risk_types,
        "reason": "OpenAI Moderation 标记该内容存在风险" if flagged else "未发现明显风险",
        "provider": "openai",
        "raw": data,
    }
