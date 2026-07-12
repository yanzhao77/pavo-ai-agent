import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Pavo AI Agent"
    app_env: str = "development"
    log_level: str = "INFO"
    agnes_api_base_url: str = "https://apihub.agnes-ai.com/v1"
    agnes_api_key: str = ""
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pavo_agent"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "minio_admin"
    minio_secret_key: str = "minio_secret"
    minio_bucket: str = "pavo-videos"
    max_concurrent_video_jobs: int = 3
    video_timeout_seconds: int = 300
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
