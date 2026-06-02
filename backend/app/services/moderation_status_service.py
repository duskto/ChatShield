import asyncio

from app.config import get_settings
from app.schemas.system import StatusResponse
from app.services.api_moderation import moderate_text
from app.utils.time import elapsed_ms, utc_now


_CACHE_TTL_MS = 60_000
_status_cache: dict[str, object] = {
    "value": None,
    "checked_at": None,
}
_status_lock = asyncio.Lock()


def _cached_status_is_fresh() -> bool:
    checked_at = _status_cache.get("checked_at")
    if checked_at is None:
        return False
    return elapsed_ms(checked_at, utc_now()) < _CACHE_TTL_MS


def _build_disabled_status() -> StatusResponse:
    settings = get_settings()
    return StatusResponse(
        available=False,
        provider=settings.moderation_provider,
        message="API 审核已禁用",
    )


async def _check_moderation_status() -> StatusResponse:
    settings = get_settings()
    if not settings.enable_api_moderation:
        return _build_disabled_status()

    result = await moderate_text("你好，这是一条状态检查消息", stage="status")
    available = result.get("provider") not in {None, "none"} and not result.get("error")
    return StatusResponse(
        available=available,
        provider=settings.moderation_provider,
        message=result.get("error") or result.get("reason", "审核服务可用"),
    )


async def get_moderation_status(force_refresh: bool = False) -> StatusResponse:
    settings = get_settings()
    if not settings.enable_api_moderation:
        return _build_disabled_status()

    cached = _status_cache.get("value")
    if not force_refresh and cached is not None and _cached_status_is_fresh():
        return cached  # type: ignore[return-value]

    async with _status_lock:
        cached = _status_cache.get("value")
        if not force_refresh and cached is not None and _cached_status_is_fresh():
            return cached  # type: ignore[return-value]

        status = await _check_moderation_status()
        _status_cache["value"] = status
        _status_cache["checked_at"] = utc_now()
        return status
