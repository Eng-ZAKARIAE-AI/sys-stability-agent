from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = Field(default="openrouter")

    openrouter_api_key: str = Field(default="")
    openrouter_model: str = Field(default="openai/gpt-4o-mini")
    openrouter_site_url: str = Field(default="http://localhost")
    openrouter_app_name: str = Field(default="sys-stability-agent")

    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.5-flash")

    cpu_anomaly_threshold: float = Field(default=75.0)
    log_level: str = Field(default="INFO")
    audit_log_path: str = Field(default="logs/interventions.jsonl")


settings = Settings()
