from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "LG ThinQ-Sales API"
    version: str = "0.1.0"
    demo_mode: bool = True
    llm_provider: str = "demo"
    database_url: str = "postgresql+psycopg://lg_thinq:lg_thinq@localhost:5432/lg_thinq_sales"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def allowed_origins(self) -> list[str]:
        return self.cors_origins


settings = Settings()
