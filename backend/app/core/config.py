import warnings
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    PostgresDsn,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    if isinstance(v, list | str):
        return v
    raise ValueError(v)


_INSECURE_SECRETS = frozenset(
    {"changethis", "minioadmin", "admin", "password", "secret"}
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    PROJECT_NAME: str = "Car Sales"
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "changethis"
    REFRESH_SECRET_KEY: str = "changethis"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    TOKEN_TYPE_ACCESS: str = "access"
    TOKEN_TYPE_REFRESH: str = "refresh"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "car_sales"

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 5
    DB_POOL_RECYCLE: int = 3600

    DB_DRIVER: Literal["asyncpg", "psycopg"] = "asyncpg"
    DB_SSL_MODE: Literal[
        "disable", "allow", "prefer", "require", "verify-ca", "verify-full"
    ] = "disable"

    USE_PGBOUNCER: bool = False
    PGBOUNCER_HOST: str = "pgbouncer"
    PGBOUNCER_PORT: int = 6432

    TRUST_PROXY_HEADERS: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def _async_scheme(self) -> str:
        return f"postgresql+{self.DB_DRIVER}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> PostgresDsn:
        host = self.PGBOUNCER_HOST if self.USE_PGBOUNCER else self.POSTGRES_SERVER
        port = self.PGBOUNCER_PORT if self.USE_PGBOUNCER else self.POSTGRES_PORT
        return PostgresDsn.build(
            scheme=self._async_scheme,
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=host,
            port=port,
            path=self.POSTGRES_DB,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_sync_database_uri(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_USE_TLS: bool = False
    REDIS_MAX_CONNECTIONS: int = 20

    CACHE_ENABLED: bool = True

    AI_BACKEND: Literal["docker", "local"] = "docker"

    OLLAMA_DOCKER_URL: str = "http://ollama:11434"
    OLLAMA_LOCAL_URL: str = "http://host.docker.internal:11434"

    OLLAMA_BASE_URL: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ollama_url(self) -> str:
        if self.OLLAMA_BASE_URL:
            return self.OLLAMA_BASE_URL
        if self.AI_BACKEND == "local":
            return self.OLLAMA_LOCAL_URL
        return self.OLLAMA_DOCKER_URL

    AI_MODEL_NAME: str = "qwen3.5:0.8b"

    AI_REQUEST_TIMEOUT_SEC: float = 120.0
    AI_CONNECT_TIMEOUT_SEC: float = 10.0
    AI_WRITE_TIMEOUT_SEC: float = 30.0
    AI_POOL_TIMEOUT_SEC: float = 10.0

    AI_TEMPERATURE: float = 0.3

    AI_NUM_PREDICT: int = 1024

    AI_NUM_CTX: int = 4096

    AI_MAX_TOOL_CALL_ROUNDS: int = 3
    AI_MAX_HISTORY_MESSAGES: int = 6

    AI_MAX_REQUESTS_PER_MINUTE: int = 5
    AI_RATE_LIMIT_WINDOW_SEC: int = 60

    AI_TOOL_DB_TIMEOUT_SEC: float = 10.0
    AI_TOOL_MAX_RESULTS: int = 10

    UPLOAD_DIR: str = "uploads"
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"

    IMAGE_MAX_DIMENSION: int = 1920
    IMAGE_THUMB_DIMENSION: int = 640
    IMAGE_MAX_PIXELS_MP: int = 30
    IMAGE_JPEG_QUALITY: int = 85
    IMAGE_THUMB_QUALITY: int = 75

    IMAGE_MAX_PER_CAR: int = 20
    IMAGE_MIN_PER_OFFER: int = 3
    IMAGE_MAX_PER_OFFER: int = 20

    @computed_field  # type: ignore[prop-decorator]
    @property
    def image_max_pixels(self) -> int:
        return self.IMAGE_MAX_PIXELS_MP * 1_000_000

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_image_types_list(self) -> list[str]:
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",")]

    PAGINATION_DEFAULT_LIMIT: int = 20
    PAGINATION_MAX_LIMIT: int = 100

    FIRST_SUPERUSER_EMAIL: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "changethis"
    FIRST_SUPERUSER_FULL_NAME: str = "System Administrator"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(o).rstrip("/") for o in self.BACKEND_CORS_ORIGINS]

    STORAGE_BACKEND: Literal["local", "minio"] = "local"

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "car-sales"
    MINIO_SECURE: bool = False
    MINIO_PUBLIC_URL: str = "http://localhost:9000"

    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = ""
    SENTRY_RELEASE: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.0
    SENTRY_SEND_DEFAULT_PII: bool = False

    YOOKASSA_SHOP_ID: str = ""
    YOOKASSA_SECRET_KEY: str = ""
    YOOKASSA_RETURN_URL: str = "https://example.com/api/v1/payments/return"
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    SMS_BACKEND: Literal["fake", "exolve"] = "fake"
    EXOLVE_API_KEY: str = ""
    EXOLVE_FROM_NUMBER: str = ""
    EXOLVE_BASE_URL: str = "https://api.exolve.ru"

    OTP_TTL_SECONDS: int = 600
    OTP_COOLDOWN_SECONDS: int = 60
    OTP_LOCKOUT_SECONDS: int = 900
    OTP_MAX_ATTEMPTS: int = 3
    OTP_MAX_DAILY: int = 5

    MAX_ACTIVE_LISTINGS: int = 5
    LISTING_LIFETIME_DAYS: int = 30
    RESERVATION_HOLD_DAYS: int = 5

    RESERVATION_DEPOSIT_AMOUNT: int = 5000
    DEPOSIT_PAYMENT_TTL_MINUTES: int = 30
    OUTCOME_PROMPT_INTERVAL_HOURS: int = 24
    OUTCOME_CORRECTION_HOURS: int = 24
    MAX_FAVORITES: int = 300

    MAX_ACTIVE_RESERVATIONS_PER_BUYER: int = 2
    EARLY_CANCEL_WINDOW_SECONDS: int = 600
    EARLY_CANCEL_COOLDOWN_SECONDS: int = 86400
    REFUND_DELAY_WINDOW_SECONDS: int = 30 * 24 * 3600
    REFUND_DELAY_TIERS_SECONDS: str = "0,3600,21600,86400,259200"

    CITIES_POPULAR_LIMIT: int = 15

    PUBLIC_BROWSE_RATE_LIMIT: int = 120
    PUBLIC_BROWSE_RATE_WINDOW: int = 60

    SCHEDULER_ENABLED: bool = True
    SCHEDULER_EXPIRE_LISTINGS_INTERVAL_SECONDS: int = 3600
    SCHEDULER_RELEASE_EXPIRED_INTERVAL_SECONDS: int = 300
    SCHEDULER_FINALIZE_SETTLING_INTERVAL_SECONDS: int = 300
    SCHEDULER_OUTCOME_PROMPTS_INTERVAL_SECONDS: int = 1800
    SCHEDULER_RECONCILE_DEPOSITS_INTERVAL_SECONDS: int = 300

    @computed_field  # type: ignore[prop-decorator]
    @property
    def refund_delay_tiers(self) -> list[int]:
        return [int(s) for s in self.REFUND_DELAY_TIERS_SECONDS.split(",") if s.strip()]

    @field_validator("REFUND_DELAY_TIERS_SECONDS")
    @classmethod
    def _validate_refund_tiers(cls, v: str) -> str:
        parts = [s.strip() for s in v.split(",") if s.strip()]
        if not parts:
            raise ValueError("REFUND_DELAY_TIERS_SECONDS must list at least one tier")
        for p in parts:
            n = int(p)
            if n < 0:
                raise ValueError("refund delay tier must be non-negative")
        return v

    @field_validator("SENTRY_TRACES_SAMPLE_RATE", "SENTRY_PROFILES_SAMPLE_RATE")
    @classmethod
    def _validate_sentry_sample_rate(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Sentry sample rate должен быть в диапазоне [0.0, 1.0]")
        return v

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value in _INSECURE_SECRETS:
            msg = (
                f'Значение переменной {var_name} небезопасно: "{value}". '
                "Измените значение перед деплоем!"
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(msg, stacklevel=1)
            else:
                raise ValueError(msg)

    @field_validator("IMAGE_JPEG_QUALITY", "IMAGE_THUMB_QUALITY")
    @classmethod
    def _validate_quality(cls, v: int) -> int:
        if not (1 <= v <= 95):
            raise ValueError("Качество JPEG должно быть от 1 до 95")
        return v

    @field_validator("RESERVATION_HOLD_DAYS")
    @classmethod
    def _hold_days_within_bank_cap(cls, v: int) -> int:
        if not (1 <= v <= 7):
            raise ValueError(
                "RESERVATION_HOLD_DAYS must be 1..7 "
                "(YooKassa two-stage hold is capped at 7 days)"
            )
        return v

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )
        self._check_default_secret("REFRESH_SECRET_KEY", self.REFRESH_SECRET_KEY)
        self._check_default_secret("MINIO_ACCESS_KEY", self.MINIO_ACCESS_KEY)
        self._check_default_secret("MINIO_SECRET_KEY", self.MINIO_SECRET_KEY)

        if self.ENVIRONMENT == "production" and not self.all_cors_origins:
            raise ValueError(
                "BACKEND_CORS_ORIGINS must be set in production. "
                "Never use wildcard '*' in production CORS settings."
            )

        if self.ENVIRONMENT == "production" and self.SENTRY_SEND_DEFAULT_PII:
            raise ValueError(
                "SENTRY_SEND_DEFAULT_PII должен быть False в проде "
                "официальная документация по умолчанию ставит True, "
                "но это шлёт IP/cookies/auth-заголовки в Sentry (так низя)"
            )
        return self


settings = Settings()
