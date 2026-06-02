from typing import Any

from app.config import get_settings
from app.services.deepseek_moderation import moderate_with_deepseek
from app.services.risk_engine import build_safe_result


def build_fallback_result(error: str) -> dict[str, Any]:
    result = build_safe_result(reason="API 审核失败，已降级为本地规则检测", provider="none")
    result["error"] = error
    return result


async def moderate_text(text: str, stage: str = "input", require_strict_classification: bool = False) -> dict[str, Any]:
    settings = get_settings()
    if not settings.enable_api_moderation:
        return build_safe_result(reason="API 审核已禁用", provider="none")
    if not text or not text.strip():
        return build_safe_result(provider="none")

    try:
        return await moderate_with_deepseek(text, require_strict_classification=require_strict_classification)
    except Exception as exc:  # noqa: BLE001
        return build_fallback_result(f"{stage} moderation failed: {exc}")
