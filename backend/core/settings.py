from functools import lru_cache
from typing import Literal, Self

from pydantic import EmailStr, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        case_sensitive=False,
    )

    postgresql_host: str
    postgresql_port: int = Field(gt=0, le=65535)
    postgresql_user: str = Field(min_length=1)
    postgresql_password: SecretStr
    postgresql_db: str = Field(min_length=1)

    openai_api_key: SecretStr | None = None
    openai_model: str | None = None
    openai_timeout_seconds: float = Field(default=5.0, gt=0, le=30)

    smtp_host: str | None = None
    smtp_port: int = Field(default=587, gt=0, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_sender_email: EmailStr | None = None
    smtp_owner_email: EmailStr | None = None
    smtp_start_tls: bool = True
    smtp_use_tls: bool = False
    smtp_timeout_seconds: float = Field(default=10.0, gt=0, le=30)

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file: str = "logs/app.log"
    log_max_bytes: int = Field(default=5_000_000, gt=0)
    log_backup_count: int = Field(default=5, ge=0)

    rate_limit_requests: int = Field(default=5, gt=0)
    rate_limit_window_seconds: int = Field(default=900, gt=0)
    trust_proxy_headers: bool = False

    cors_origins: list[str] = Field(default_factory=list)
    metrics_api_key: SecretStr | None = None

    @model_validator(mode="after")
    def validate_smtp_tls_modes(self) -> Self:
        if self.smtp_start_tls and self.smtp_use_tls:
            raise ValueError("SMTP_START_TLS and SMTP_USE_TLS cannot both be enabled")
        return self

    @property
    def postgresql_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgresql_user,
            password=self.postgresql_password.get_secret_value(),
            host=self.postgresql_host,
            port=self.postgresql_port,
            database=self.postgresql_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
