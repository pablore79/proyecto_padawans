from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Bunker4 Alumnos Frontend"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Backend API URL
    BACKEND_URL: str = "http://backend:8000"

    # Frontend settings
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


settings = Settings()
