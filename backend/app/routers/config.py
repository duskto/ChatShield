from fastapi import APIRouter

from app.config import get_settings
from app.schemas.system import ModelListResponse, StatusResponse, SystemConfigResponse
from app.services.api_moderation import moderate_text
from app.services.ollama_service import get_ollama_status, list_ollama_models

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("", response_model=SystemConfigResponse)
def get_system_config() -> SystemConfigResponse:
    settings = get_settings()
    return SystemConfigResponse(
        app_name=settings.app_name,
        environment=settings.app_env,
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        moderation_provider=settings.moderation_provider,
        enable_rule_check=settings.enable_rule_check,
        enable_api_moderation=settings.enable_api_moderation,
        input_block_threshold=settings.input_block_threshold,
        output_block_threshold=settings.output_block_threshold,
    )


@router.get("/ollama/status", response_model=StatusResponse)
async def ollama_status() -> StatusResponse:
    result = await get_ollama_status()
    return StatusResponse(
        available=result["available"],
        provider=result["provider"],
        message=result["message"],
        models=result.get("models", []),
    )


@router.get("/moderation/status", response_model=StatusResponse)
async def moderation_status() -> StatusResponse:
    settings = get_settings()
    result = await moderate_text("你好，这是一条状态检查消息", stage="status")
    available = settings.enable_api_moderation and result.get("provider") not in {None, "none"}
    if result.get("error"):
        available = False
    return StatusResponse(
        available=available,
        provider=settings.moderation_provider,
        message=result.get("error") or result.get("reason", "审核服务可用"),
    )


@router.get("/models", response_model=ModelListResponse)
async def ollama_models() -> ModelListResponse:
    result = await list_ollama_models()
    return ModelListResponse(
        default_model=result["default_model"],
        models=result["models"],
    )
