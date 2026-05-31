from typing import Any

from app.config import get_settings
from app.services.deepseek_moderation import moderate_with_deepseek
from app.services.openai_moderation import moderate_with_openai
from app.services.risk_engine import build_safe_result


def build_fallback_result(error: str) -> dict[str, Any]:
    result = build_safe_result(reason="API 审核失败，已降级为本地规则检测", provider="none")
    result["error"] = error
    return result


async def moderate_text(text: str, stage: str = "input") -> dict[str, Any]:
    settings = get_settings()
    if not settings.enable_api_moderation:
        return build_safe_result(reason="API 审核已禁用", provider="none")
    if not text or not text.strip():
        return build_safe_result(provider="none")

    provider = settings.moderation_provider.lower().strip()
    try:
        if provider == "deepseek":
            return await moderate_with_deepseek(text)
        if provider == "openai":
            return await moderate_with_openai(text)
        return build_fallback_result(f"未知审核提供商: {provider}")
    except Exception as exc:  # noqa: BLE001
        return build_fallback_result(f"{stage} moderation failed: {exc}")

