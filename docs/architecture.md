# Архитектура

`tg_diary` — Telegram diary bot с явным разделением слоёв: обработка
Telegram updates, бизнес-логика в services, persistence через SQLAlchemy,
FSM state в Redis, фоновые reminders через Celery и небольшой observability
HTTP server.

## Bot flow

```text
Telegram user
    |
    v
aiogram Bot / Dispatcher
    |
    v
routers in app/handlers
    |
    v
services in app/services
    |
    +--> SQLAlchemy session factory
    +--> Redis FSM storage
    +--> Telegram API responses
```

1. `app.main` загружает environment variables, валидирует config, настраивает
   JSON logs, включает Sentry при наличии DSN и запускает observability server.
2. Dispatcher регистрирует feature routers из `app/handlers`.
3. Handlers оставляют Telegram-specific orchestration рядом с aiogram и
   делегируют операции с данными, reminders, backups, questions и speech-related
   задачи в services.
4. Services используют process-level SQLAlchemy session factory из
   `app.storage`.
5. FSM state хранится в Redis, поэтому многошаговые сценарии переживают restart
   процесса и могут использоваться bot-процессом и кодом доставки reminders.

## DB и session flow

```text
Config DATABASE_URL
    |
    v
create_session_factory
    |
    v
Session per handler/service operation
    |
    v
SQLAlchemy models
    |
    v
PostgreSQL or SQLite
```

Для локальной разработки можно использовать SQLite, а Docker и production-like
запуск ориентированы на PostgreSQL. Изменения схемы управляются Alembic
migrations из `migrations/versions`.

Migrations намеренно вынесены в отдельный operational step:

```bash
python -m app.migrate
```

`RUN_MIGRATIONS_ON_STARTUP=true` подходит для небольших self-hosted запусков,
но по умолчанию выключен, чтобы не связывать application startup с обновлением
DB schema.

## Celery flow

```text
Celery beat
    |
    v
enqueue_due_reminders every minute
    |
    v
list due users in DB
    |
    v
process_user_reminders tasks
    |
    +--> DB: resolve due reminder types and update next_due_at
    +--> Redis FSM: prepare entry state when needed
    +--> Telegram API: send reminder messages
```

Celery по умолчанию использует Redis как broker и result backend. Процесс beat
каждую минуту планирует `app.tasks.reminders.enqueue_due_reminders`. Эта task
ищет пользователей с наступившим `next_due_at` и создаёт отдельные
`process_user_reminders` jobs для каждого пользователя.

Per-user jobs рассчитывают daily, weekly и monthly reminders в timezone
пользователя, отправляют Telegram messages, выставляют ожидаемый FSM state для
prompt-based diary entry и сохраняют следующий due timestamp.

## Observability flow

```text
Application processes
    |
    +--> JSON logs to stdout
    +--> Sentry SDK when SENTRY_DSN is set
    +--> in-process Prometheus counters and histograms
            |
            v
        /metrics on observability HTTP server

Health checks
    |
    v
/health or /healthz
```

Bot-процесс запускает background HTTP server на `OBSERVABILITY_HOST` и
`OBSERVABILITY_PORT`. Он отдаёт `/health`, `/healthz` и `/metrics`.

Metrics реализованы in-process и покрывают bot startups, polling exceptions,
результаты reminder tasks, external API errors, Celery retries, emitted alerts и
processing duration buckets.