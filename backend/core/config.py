import os
import logging
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Force load .env from current directory or backend/.env, overriding any stale environment variables
env_paths = [".env", "backend/.env", "../backend/.env"]
for ep in env_paths:
    if os.path.exists(ep):
        load_dotenv(ep, override=True)

_DEFAULT_SECRET = "CHANGE_ME_IN_PRODUCTION_DO_NOT_USE_THIS_KEY"


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Data Quality & Profiling Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # "development", "test", "production"
    LOG_LEVEL: str = "INFO"

    # SECURITY: Must be overridden via environment variable in production.
    SECRET_KEY: str = _DEFAULT_SECRET
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = "sqlite:///../database/data_quality.db"
    UPLOAD_DIR: str = "./uploads"
    CLEANED_DIR: str = "./cleaned_datasets"
    REPORTS_DIR: str = "./reports"
    VECTOR_DB_DIR: str = "./vector_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"

    # Performance & Concurrency Tuning
    MAX_UPLOAD_SIZE_MB: int = 100
    CELERY_WORKER_CONCURRENCY: int = 4
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # CORS: Comma-separated list of allowed origins. Override in production.
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # SMTP Settings — must come from environment, never hardcoded
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM: str = ""

    # Document & RAG Storage Settings
    DOCUMENTS_DIR: str = "./documents"
    EMBEDDING_PROVIDER: str = "sentence-transformers"  # "sentence-transformers", "openai", "fallback"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32

    # LLM Settings
    LLM_PROVIDER: str = "openai"  # "openai", "ollama", "mock"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 1024
    LLM_TIMEOUT: int = 30
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Vector Store & RAG Retrieval
    VECTOR_STORE_TYPE: str = "pgvector"  # "pgvector", "in_memory"
    TOP_K_VECTOR: int = 10
    TOP_K_BM25: int = 10
    TOP_K_FINAL: int = 5


    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

    def validate_production_secrets(self) -> None:
        """Enforce strict fail-fast validation in production environment."""
        if self.ENVIRONMENT.lower() == "production":
            if self.SECRET_KEY == _DEFAULT_SECRET:
                raise RuntimeError(
                    "FATAL SECURITY ERROR: ENVIRONMENT is 'production' but SECRET_KEY is set to the default insecure value! "
                    "Set a secure SECRET_KEY environment variable before deploying to production."
                )
        elif self.SECRET_KEY == _DEFAULT_SECRET:
            logger.warning(
                "SECURITY WARNING: SECRET_KEY is using the default insecure value. "
                "Set the SECRET_KEY environment variable before deploying to production."
            )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
settings.validate_production_secrets()
