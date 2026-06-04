from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="ChatShield", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    database_url: str = Field(default="sqlite:///./chatshield.db", alias="DATABASE_URL")

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:3b", alias="OLLAMA_MODEL")
    ollama_timeout: int = Field(default=120, alias="OLLAMA_TIMEOUT")
    ollama_keep_alive: str = Field(default="24h", alias="OLLAMA_KEEP_ALIVE")
    ollama_model_start_timeout: int = Field(default=30, alias="OLLAMA_MODEL_START_TIMEOUT")

    enable_rule_check: bool = Field(default=True, alias="ENABLE_RULE_CHECK")
    enable_api_moderation: bool = Field(default=True, alias="ENABLE_API_MODERATION")
    moderation_provider: str = "deepseek"

    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

    input_block_threshold: str = Field(default="high", alias="INPUT_BLOCK_THRESHOLD")
    output_block_threshold: str = Field(default="high", alias="OUTPUT_BLOCK_THRESHOLD")
    save_raw_text: bool = Field(default=True, alias="SAVE_RAW_TEXT")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
