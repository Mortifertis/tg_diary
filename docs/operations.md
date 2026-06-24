# Operations

Этот документ описывает local development, Docker-based запуск, migrations,
environment configuration, backups, release/packages и troubleshooting для
`tg_diary`.

## Local development

Рекомендуемая версия Python: 3.12.x.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
python -m app.migrate
python -m app.main
```

Для Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
copy .env.example .env
python -m app.migrate
python -m app.main
```

Для optional voice recognition установите `ffmpeg`, затем отдельный набор
voice dependencies:

```bash
pip install -r requirements-voice.txt
```

## Docker Compose

Docker Compose запускает PostgreSQL, Redis, отдельный migration job, bot,
Celery worker и Celery beat:

```bash
cp .env.docker.example .env.docker
make docker-up
```

Остановить stack можно командой:

```bash
make docker-down
```

Сервис `migrate` ждёт healthy PostgreSQL и должен успешно завершиться до старта
bot и Celery services.

## Migrations

Рекомендуемая команда:

```bash
python -m app.migrate
```

Альтернативный прямой вызов Alembic:

```bash
alembic upgrade head
```

Для небольших self-hosted installations можно включить startup migrations:

```env
RUN_MIGRATIONS_ON_STARTUP=true
```

Для production-like deployments лучше держать этот режим выключенным, чтобы
migrations оставались контролируемым release step.

## Environment variables

Для local development используйте `.env.example`, для Docker Compose —
`.env.docker.example`. Основные настройки:

| Variable | Назначение |
| --- | --- |
| `APP_ENV` | Имя runtime environment. В production валидация строже. |
| `BOT_TOKEN` | Telegram bot token. |
| `DATABASE_URL` | SQLAlchemy database URL. |
| `REDIS_URL` | Redis URL для FSM state. |
| `CELERY_BROKER_URL` | Celery broker URL. По умолчанию равен `REDIS_URL`. |
| `CELERY_RESULT_BACKEND` | Celery result backend URL. По умолчанию `REDIS_URL`. |
| `LOG_LEVEL` | Root logging level. |
| `SENTRY_DSN` | Включает Sentry, если значение не пустое. |
| `OBSERVABILITY_HOST` | Bind host для health и metrics. |
| `OBSERVABILITY_PORT` | Port для health и metrics. `0` или меньше отключает server. |
| `RUN_MIGRATIONS_ON_STARTUP` | Optional automatic migration switch. |

## Backup и restore

В bot есть archive-oriented backup/export services. Generated archives содержат
settings, database content и attachment manifest. Для operational PostgreSQL
backups дополнительно нужны регулярные database-level dumps, например:

```bash
pg_dump "$DATABASE_URL" > tg_diary.sql
```

В Docker Compose данные PostgreSQL лежат в named volume `db_data`. Делайте
backup этого volume или запускайте `pg_dump` из container, подключённого к той
же network.

## Release и packages

В repository есть release workflow, который срабатывает на semver tags формата
`vMAJOR.MINOR.PATCH`. Для валидного tag он создаёт GitHub Release, выполняет
login в GHCR, затем builds и pushes Docker image с тегами exact version,
`MAJOR.MINOR`, `MAJOR` и `latest`.

После push release tag проверьте GitHub Actions release workflow и repository
Packages page. Если package не появился, смотрите release job logs, особенно
шаги GHCR authentication и image push.

## Troubleshooting

### Bot не стартует

* Проверьте, что `BOT_TOKEN` задан и не равен placeholder value.
* Проверьте `DATABASE_URL` и выполните `python -m app.migrate`.
* Проверьте доступность Redis и значение `REDIS_URL`.

### Docker services не стартуют

* Выполните `docker compose ps`, чтобы посмотреть service state.
* Проверьте migration logs: `docker compose logs migrate`.
* Проверьте database readiness: `docker compose logs db`.

### Reminders не доставляются

* Убедитесь, что `celery_worker` и `celery_beat` запущены.
* Проверьте Redis connectivity для Celery broker и result backend.
* Посмотрите Celery logs на retry или alert messages.
* Проверьте timezone пользователя и reminder settings в database.

### Metrics или health checks недоступны

* Убедитесь, что `OBSERVABILITY_PORT` больше нуля.
* Проверьте, что port проброшен runtime environment, если запуск идёт в
  container.
* Сначала запросите `/health`, затем `/metrics`.