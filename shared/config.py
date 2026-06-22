from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    VALKEY_URL: str = "redis://127.0.0.1:6379"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost/quemvota"
    EMBEDDING_DIMENSION: int = 1024
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
