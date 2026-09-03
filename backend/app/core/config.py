from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ozen_user:password@localhost:5432/ozen_lms"

    # JWT
    SECRET_KEY: str = "change_me_very_secret_key_at_least_32_chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS — comma-separated string in .env
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:80"

    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_PATH: str = "/app/storage"
    MAX_UPLOAD_SIZE_MB: int = 50
    # Course materials (video/PDF/presentations) allow bigger files — keep in
    # sync with `client_max_body_size` in docker/nginx/nginx.prod.conf.
    MAX_MATERIAL_SIZE_MB: int = 500

    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True


settings = Settings()

_DEFAULT_SECRET_KEY = "change_me_very_secret_key_at_least_32_chars"
if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == _DEFAULT_SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is still the default placeholder value while ENVIRONMENT=production. "
        "Set a real, secret SECRET_KEY in your .env before starting the app — "
        "otherwise anyone can forge admin JWT tokens."
    )
