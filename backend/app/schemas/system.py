from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str


class SystemConfigResponse(BaseModel):
    app_name: str
    environment: str
    ollama_base_url: str
    ollama_model: str
    moderation_provider: str
    enable_rule_check: bool
    enable_api_moderation: bool
    input_block_threshold: str
    output_block_threshold: str


class StatusResponse(BaseModel):
    available: bool
    provider: str
    message: str
    models: list[str] = []


class ModelListResponse(BaseModel):
    default_model: str
    models: list[str]
