"""Configurações globais do projeto."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    search_max_results: int = 5
    search_timeout: int = 30
    log_level: str = "INFO"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: str = "anthropic"
    redacao_max_tokens: int = 4096


settings = Settings()
