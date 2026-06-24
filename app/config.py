from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

BOT_TOKEN_PLACEHOLDER = "replace-with-telegram-bot-token"
PLACEHOLDER_VALUES = {"", BOT_TOKEN_PLACEHOLDER}
PRODUCTION_ENVIRONMENTS = {"prod", "production"}


@dataclass(slots=True)
class Config:
    app_env: str
    bot_token: str
    database_url: str
    redis_url: str
    redis_connect_retries: int
    redis_retry_delay_seconds: float
    timezone: str
    daily_time_default: str
    weekly_day_default: int
    weekly_time_default: str
    monthly_day_default: int
    monthly_time_default: str
    reminder_evening_hour: int
    whisper_model: str
    whisper_device: str
    celery_broker_url: str
    celery_result_backend: str
    log_level: str
    sentry_dsn: str
    sentry_environment: str
    sentry_traces_sample_rate: float
    observability_host: str
    observability_port: int
    run_migrations_on_startup: bool


def _get_numeric_env[T: (int, float)](
    name: str,
    default: T,
    parser: Callable[[str], T],
) -> T:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return parser(raw_value)
    except (TypeError, ValueError):
        return default


def _get_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> Config:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Config(
        app_env=os.getenv("APP_ENV", "dev"),
        bot_token=os.getenv("BOT_TOKEN", ""),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./tg_diary.db"),
        redis_url=redis_url,
        redis_connect_retries=_get_numeric_env(
            name="REDIS_CONNECT_RETRIES",
            default=5,
            parser=int,
        ),
        redis_retry_delay_seconds=_get_numeric_env(
            name="REDIS_RETRY_DELAY_SECONDS",
            default=1.0,
            parser=float,
        ),
        timezone=os.getenv("DEFAULT_TIMEZONE", "UTC"),
        daily_time_default=os.getenv("DEFAULT_DAILY_TIME", "09:00"),
        weekly_day_default=_get_numeric_env(
            name="DEFAULT_WEEKLY_DAY",
            default=6,
            parser=int,
        ),
        weekly_time_default=os.getenv("DEFAULT_WEEKLY_TIME", "20:00"),
        monthly_day_default=_get_numeric_env(
            name="DEFAULT_MONTHLY_DAY",
            default=1,
            parser=int,
        ),
        monthly_time_default=os.getenv("DEFAULT_MONTHLY_TIME", "20:00"),
        reminder_evening_hour=_get_numeric_env(
            name="REMINDER_EVENING_HOUR",
            default=20,
            parser=int,
        ),
        whisper_model=os.getenv("WHISPER_MODEL", "small"),
        whisper_device=os.getenv("WHISPER_DEVICE", "cpu"),
        celery_broker_url=os.getenv(
            "CELERY_BROKER_URL",
            redis_url,
        ),
        celery_result_backend=os.getenv(
            "CELERY_RESULT_BACKEND",
            redis_url,
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        sentry_dsn=os.getenv("SENTRY_DSN", ""),
        sentry_environment=os.getenv("SENTRY_ENVIRONMENT", "dev"),
        sentry_traces_sample_rate=_get_numeric_env(
            name="SENTRY_TRACES_SAMPLE_RATE",
            default=0.0,
            parser=float,
        ),
        observability_host=os.getenv("OBSERVABILITY_HOST", "0.0.0.0"),
        observability_port=_get_numeric_env(
            name="OBSERVABILITY_PORT",
            default=8001,
            parser=int,
        ),
        run_migrations_on_startup=_get_bool_env(
            name="RUN_MIGRATIONS_ON_STARTUP",
            default=False,
        ),
    )


def _is_placeholder(value: str) -> bool:
    return value.strip() in PLACEHOLDER_VALUES


def validate_config(config: Config) -> None:
    if _is_placeholder(config.bot_token):
        raise RuntimeError("BOT_TOKEN must be configured")

    if config.app_env.strip().lower() not in PRODUCTION_ENVIRONMENTS:
        return

    required_values = {
        "DATABASE_URL": config.database_url,
        "REDIS_URL": config.redis_url,
        "CELERY_BROKER_URL": config.celery_broker_url,
    }
    invalid_names = [
        name
        for name, value in required_values.items()
        if _is_placeholder(value)
    ]
    if invalid_names:
        names = ", ".join(invalid_names)
        raise RuntimeError(f"{names} must be configured in production")
