import socket
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    VALKEY_URL: str = "redis://127.0.0.1:6379"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost/quemvota"
    EMBEDDING_DIMENSION: int = 1024
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def fallback_localhost(cls, v: str) -> str:
        if "@postgres:" in v:
            try:
                socket.gethostbyname("postgres")
            except socket.gaierror:
                return v.replace("@postgres:", "@127.0.0.1:")
        return v


settings = Settings()
