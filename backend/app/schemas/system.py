from pydantic import BaseModel, Field


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
    models: list[str] = Field(default_factory=list)


class ModelListResponse(BaseModel):
    default_model: str
    models: list[str]


class SystemBootstrapResponse(BaseModel):
    config: SystemConfigResponse
    ollama_status: StatusResponse
    moderation_status: StatusResponse
    models: ModelListResponse
