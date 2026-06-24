import pytest

from app.config import load_config, validate_config


def test_load_config_uses_defaults_for_invalid_numeric_env(
    monkeypatch,
) -> None:
    monkeypatch.setenv("REDIS_CONNECT_RETRIES", "invalid")
    monkeypatch.setenv("REDIS_RETRY_DELAY_SECONDS", "invalid")
    monkeypatch.setenv("DEFAULT_WEEKLY_DAY", "bad")
    monkeypatch.setenv("DEFAULT_MONTHLY_DAY", "bad")
    monkeypatch.setenv("REMINDER_EVENING_HOUR", "bad")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "bad")
    monkeypatch.setenv("OBSERVABILITY_PORT", "bad")
    monkeypatch.delenv("RUN_MIGRATIONS_ON_STARTUP", raising=False)

    config = load_config()

    assert config.redis_connect_retries == 5
    assert config.redis_retry_delay_seconds == 1.0
    assert config.weekly_day_default == 6
    assert config.monthly_day_default == 1
    assert config.reminder_evening_hour == 20
    assert config.sentry_traces_sample_rate == 0.0
    assert config.observability_port == 8001
    assert config.run_migrations_on_startup is False


def test_load_config_reuses_redis_url_for_celery(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://test:6379/2")
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    monkeypatch.delenv("CELERY_RESULT_BACKEND", raising=False)

    config = load_config()

    assert config.celery_broker_url == "redis://test:6379/2"
    assert config.celery_result_backend == "redis://test:6379/2"


def test_load_config_reads_migration_startup_flag(monkeypatch) -> None:
    monkeypatch.setenv("RUN_MIGRATIONS_ON_STARTUP", "true")

    config = load_config()

    assert config.run_migrations_on_startup is True


@pytest.mark.parametrize(
    "bot_token",
    ["", "replace-with-telegram-bot-token"],
)
def test_validate_config_rejects_missing_or_placeholder_bot_token(
    bot_token,
    monkeypatch,
) -> None:
    monkeypatch.setenv("BOT_TOKEN", bot_token)

    config = load_config()

    with pytest.raises(RuntimeError, match="BOT_TOKEN must be configured"):
        validate_config(config)


def test_validate_config_allows_configured_bot_token(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123:real-token")

    config = load_config()

    validate_config(config)


def test_validate_config_rejects_production_placeholders(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BOT_TOKEN", "123:real-token")
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("CELERY_BROKER_URL", "")

    config = load_config()

    with pytest.raises(RuntimeError) as error:
        validate_config(config)

    message = str(error.value)
    assert "DATABASE_URL" in message
    assert "REDIS_URL" in message
    assert "CELERY_BROKER_URL" in message
