from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Skill Pilot AI"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "skillpilot_hackathon_super_secret_jwt_key_change_in_production_32bytes"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # Leave blank to run without a database (AI features only)
    DATABASE_URL: str = ""

    # CORS — comma-separated string, e.g.:
    # http://localhost:5173,http://localhost:3000
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> list:
        raw = self.BACKEND_CORS_ORIGINS.strip()
        return [o.strip() for o in raw.split(",") if o.strip()]

    # xAI Grok
    XAI_API_KEY: str = ""
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    XAI_MODEL: str = "grok-2-1212"
    AI_TIMEOUT_SECONDS: int = 25

    # OpenAI fallback (optional)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TIMEOUT_SECONDS: int = 25

    @property
    def GROK_API_KEY(self) -> str:
        return self.XAI_API_KEY

    @property
    def GROK_MODEL(self) -> str:
        return self.XAI_MODEL

    @property
    def GROK_API_BASE(self) -> str:
        return self.XAI_BASE_URL

    # Cookie
    SECURE_COOKIE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # Python execution (external)
    PYTHON_EXECUTION_API_URL: str = ""
    PYTHON_EXECUTION_API_KEY: str = ""

    # File uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


def _normalize_db_url(url: str) -> str:
    """Convert postgres:// and postgresql:// to asyncpg dialect."""
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("?sslmode=require", "?ssl=require").replace("&sslmode=require", "&ssl=require")
    return url


settings = Settings()
# Normalise DB URL after construction (avoids pydantic validator issues)
settings.DATABASE_URL = _normalize_db_url(settings.DATABASE_URL)
