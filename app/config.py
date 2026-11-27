from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./knowledge.db"
    jwt_secret: SecretStr = SecretStr("development-only-change-this-secret-before-deploy")
    token_minutes: int = 30
    llm_provider: Literal["demo", "openai", "local"] = "demo"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4.1-mini"
    local_model: str = "HuggingFaceTB/SmolLM2-135M-Instruct"
    cors_origins: list[str] = ["http://localhost:3000"]
    auto_create_tables: bool = True
    llm_concurrency: int = 2
    llm_timeout_seconds: float = 60
    celery_broker_url: str = "redis://localhost:6379/0"

    @model_validator(mode="after")
    def validate_config(self) -> Self:
        if self.token_minutes <= 0 or self.llm_concurrency <= 0 or self.llm_timeout_seconds <= 0:
            raise ValueError("Token lifetime, concurrency and timeout must be positive")
        if self.environment == "production":
            if len(
                self.jwt_secret.get_secret_value()
            ) < 32 or self.jwt_secret.get_secret_value().startswith("development"):
                raise ValueError("Set a random JWT_SECRET of at least 32 characters")
            if self.auto_create_tables:
                raise ValueError("Use Alembic in production: AUTO_CREATE_TABLES=false")
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY required for OpenAI")
        return self
