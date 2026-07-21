"""Pavo configuration — settings with DB priority."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with file-based override."""
    app_name: str = "Pavo AI Agent"
    app_env: str = "development"
    log_level: str = "INFO"
    agnes_api_base_url: str = "https://apihub.agnes-ai.com/v1"
    agnes_api_key: str = ""
    pavo_home: str = str(Path.home() / ".pavo")
    static_port: int = int(os.environ.get("PORT", "18080"))
    run_mode: str = "local"
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
