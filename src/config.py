"""Configurações da aplicação via variáveis de ambiente."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Lê configurações de variáveis de ambiente ou arquivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql+asyncpg://gestor:gestor@localhost:5432/gestor_financeiro"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    app_env: str = "development"
    log_level: str = "INFO"


settings = Settings()
