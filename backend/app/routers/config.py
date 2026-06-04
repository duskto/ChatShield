import asyncio

from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.schemas.system import (
    ModelListResponse,
    ModelStartRequest,
    StatusResponse,
    SystemBootstrapResponse,
    SystemConfigResponse,
)
from app.services.moderation_status_service import get_moderation_status
from app.services.ollama_service import get_ollama_status, list_ollama_models, start_ollama_model

router = APIRouter(prefix="/api/config", tags=["config"])


def _build_system_config_response() -> SystemConfigResponse:
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


def _build_status_response(result: dict) -> StatusResponse:
    return StatusResponse(
        available=result["available"],
        provider=result["provider"],
        message=result["message"],
        models=result.get("models", []),
        running_models=result.get("running_models", []),
        active_model=result.get("active_model"),
    )


@router.get("", response_model=SystemConfigResponse)
def get_system_config() -> SystemConfigResponse:
    return _build_system_config_response()


@router.get("/ollama/status", response_model=StatusResponse)
async def ollama_status() -> StatusResponse:
    result = await get_ollama_status()
    return _build_status_response(result)


@router.get("/moderation/status", response_model=StatusResponse)
async def moderation_status(refresh: bool = Query(default=False)) -> StatusResponse:
    return await get_moderation_status(force_refresh=refresh)


@router.get("/models", response_model=ModelListResponse)
async def ollama_models() -> ModelListResponse:
    result = await list_ollama_models()
    return ModelListResponse(
        default_model=result["default_model"],
        models=result["models"],
        running_models=result.get("running_models", []),
        active_model=result.get("active_model"),
    )


@router.post("/models/start", response_model=StatusResponse)
async def start_model(request: ModelStartRequest) -> StatusResponse:
    result = await start_ollama_model(request.model)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result["message"])
    return _build_status_response(result["status"])


@router.get("/bootstrap", response_model=SystemBootstrapResponse)
async def config_bootstrap(refresh_status: bool = Query(default=False)) -> SystemBootstrapResponse:
    config = _build_system_config_response()
    ollama_result, moderation_result = await asyncio.gather(
        get_ollama_status(),
        get_moderation_status(force_refresh=refresh_status),
    )
    models = ModelListResponse(
        default_model=config.ollama_model,
        models=ollama_result.get("models", []),
        running_models=ollama_result.get("running_models", []),
        active_model=ollama_result.get("active_model"),
    )
    return SystemBootstrapResponse(
        config=config,
        ollama_status=_build_status_response(ollama_result),
        moderation_status=moderation_result,
        models=models,
    )
