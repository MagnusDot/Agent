from enum import StrEnum

from dotenv import find_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseType(StrEnum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    POSTGRES_RDS = "postgres-rds"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        validate_default=False,
    )
    MODE: str | None = None

    HOST: str = "0.0.0.0"
    PORT: int = 8080

    AUTH_SECRET: SecretStr | None = None

    OPENAI_API_KEY: SecretStr | None = None

    # Database Configuration
    DATABASE_TYPE: DatabaseType = (
        DatabaseType.SQLITE
    )  # Options: DatabaseType.SQLITE or DatabaseType.POSTGRES
    SQLITE_DB_PATH: str = "checkpoints.db"

    # PostgreSQL Configuration
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: SecretStr | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_SCHEMA: str | None = None  # Optional schema name
    POSTGRES_POOL_SIZE: int = Field(
        default=10, description="Maximum number of connections in the pool"
    )
    POSTGRES_MIN_SIZE: int = Field(
        default=3, description="Minimum number of connections in the pool"
    )
    POSTGRES_MAX_IDLE: int = Field(default=5, description="Maximum number of idle connections")
    
    def is_dev(self) -> bool:
        return self.MODE == "dev"


settings = Settings()
