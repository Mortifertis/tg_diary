# tg_diary

![CI](https://github.com/Mortifertis/tg_diary/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Docker](https://img.shields.io/badge/docker-compose-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**tg_diary** — Telegram-бот для личного дневника: короткие ежедневные записи, настроение, напоминания, ретроспективы, экспорт архива и поддержка голосовых вложений.

Проект реализован как небольшое production-minded backend-приложение: `aiogram 3`, `SQLAlchemy 2`, `Alembic`, `PostgreSQL/SQLite`, `Redis`, `Celery`, `Docker Compose`, тесты и базовая наблюдаемость.

## Какую проблему решает проект

Личный дневник часто не приживается из-за лишнего трения: нужно помнить о записях, открывать отдельное приложение, вручную возвращаться к старым заметкам и собирать итоги.

`tg_diary` снижает это трение за счёт привычного Telegram-интерфейса. Пользователь может быстро написать запись, указать настроение, получить напоминание, посмотреть последние записи, пройти ретроспективу и выгрузить архив.

## Основные возможности

* Создание коротких дневниковых записей.
* Сохранение настроения вместе с записью.
* Ежедневные, еженедельные и ежемесячные напоминания.
* Еженедельные и ежемесячные ретроспективы.
* Пользовательские ежедневные вопросы.
* Просмотр, редактирование и удаление последних записей.
* Экспорт архива дневника.
* Базовая статистика: количество записей, серия, настроение.
* Мультиязычный интерфейс: русский, английский, французский, немецкий.
* Голосовые сообщения как вложения.
* Опциональное распознавание голосовых сообщений в текст.

## Что реализовано технически

* Telegram-бот на `aiogram 3` с разделением сценариев по роутерам.
* Слой работы с данными на `SQLAlchemy 2`.
* Миграции базы данных через `Alembic`.
* Поддержка `PostgreSQL` для production-like запуска и `SQLite` для локальной разработки.
* `Redis` для хранения FSM-состояний.
* `Celery worker` и `Celery beat` для фоновых напоминаний.
* Docker Compose для локального запуска инфраструктуры.
* Unit, e2e, smoke и performance-тесты.
* Проверки качества кода через `ruff`, `mypy`, `pytest` и `pre-commit`.
* Структурированное логирование.
* Метрики Prometheus.
* Интеграционные hooks для Sentry.
* Отдельные зависимости для optional speech-to-text, чтобы не утяжелять основной runtime.

## Технические акценты

### Миграции вынесены в отдельный шаг

Основной сценарий запуска предполагает явное выполнение миграций:

```bash
python -m app.migrate
```

Автоматический запуск миграций при старте приложения доступен только при явном включении:

```env
RUN_MIGRATIONS_ON_STARTUP=true
```

Такой подход безопаснее для production-like окружения: обновление схемы базы не привязано неявно к старту бота.

### Фоновая обработка отделена от Telegram-бота

Напоминания выполняются через `Celery worker` и `Celery beat`, а не внутри основного процесса бота. Это упрощает масштабирование, перезапуск фоновых задач и контроль расписаний.

### Основной runtime не перегружен speech-to-text

Распознавание голосовых сообщений вынесено в отдельный набор зависимостей. Базовая версия проекта может работать без тяжёлых ML-библиотек.

### Код подготовлен к поддержке

Проект содержит миграции, тесты, статический анализ, pre-commit-проверки, Docker Compose и разделение бизнес-логики по сервисам. Это делает его не просто учебным скриптом, а небольшим backend-приложением, которое можно развивать дальше.

## Архитектура

```text
Пользователь Telegram
        |
        v
aiogram Bot + Routers
        |
        +--> handlers
        |       |
        |       v
        |   services
        |       |
        |       v
        |   SQLAlchemy session
        |       |
        |       v
        |   PostgreSQL / SQLite
        |
        +--> Redis FSM storage
        |
        +--> Celery beat / worker
        |       |
        |       v
        |   reminder tasks
        |       |
        |       v
        |   Telegram API
        |
        +--> Observability
                |
                +--> logs
                +--> Prometheus metrics
                +--> Sentry hooks
```

## Документация

Подробности по устройству и эксплуатации вынесены в отдельные документы:

* [Architecture](docs/architecture.md) — bot flow, DB/session flow,
  Celery flow и observability flow.
* [Operations](docs/operations.md) — локальный запуск, Docker, миграции,
  env, backup и troubleshooting.
* [Observability](docs/observability.md) — `/health`, `/metrics`, Sentry,
  JSON logs и список метрик.
* [Roadmap](docs/roadmap.md) — дальнейшие шаги развития проекта.

## Быстрый старт

Рекомендуемая версия Python: **3.12.x**.

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt

cp .env.example .env
alembic upgrade head

python -m app.main
```

Для Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt -r requirements-dev.txt

copy .env.example .env
alembic upgrade head

python -m app.main
```

## Запуск через Docker Compose

Для запуска бота вместе с инфраструктурой:

```bash
cp .env.docker.example .env.docker
make docker-up
```

Docker Compose поднимает приложение и необходимые сервисы: базу данных, Redis,
отдельный сервис миграций и фоновые процессы. Сервис миграций ждёт
готовности PostgreSQL и завершается до старта бота, `Celery worker` и
`Celery beat`.

## Миграции базы данных

Основной способ:

```bash
python -m app.migrate
```

Альтернативно можно вызвать Alembic напрямую:

```bash
alembic upgrade head
```

Для небольшого self-hosted запуска можно включить автоматическое применение миграций при старте:

```env
RUN_MIGRATIONS_ON_STARTUP=true
```

По умолчанию этот режим выключен.

## Опциональное распознавание голоса

Распознавание голосовых сообщений не входит в базовые runtime-зависимости.

Для локального speech-to-text нужно установить системный `ffmpeg`, затем дополнительные зависимости:

```bash
pip install -r requirements-voice.txt
```

Параметры распознавания задаются через переменные окружения:

```env
WHISPER_MODEL=
WHISPER_DEVICE=
```

## Проверка качества

```bash
make check
```

Отдельно можно запустить performance-тесты:

```bash
make test-performance
```

## Основные переменные окружения

Примеры конфигурации находятся в `.env.example` и `.env.docker.example`.

| Переменная                  | Назначение                                   |
| --------------------------- | -------------------------------------------- |
| `BOT_TOKEN`                 | Токен Telegram-бота                          |
| `DATABASE_URL`              | Строка подключения к базе данных             |
| `REDIS_URL`                 | Redis для FSM-состояний                      |
| `RUN_MIGRATIONS_ON_STARTUP` | Автоматический запуск миграций при старте    |
| `REDIS_CONNECT_RETRIES`     | Количество попыток подключения к Redis       |
| `REDIS_RETRY_DELAY_SECONDS` | Задержка между попытками подключения к Redis |
| `DEFAULT_TIMEZONE`          | Часовой пояс по умолчанию                    |
| `DEFAULT_DAILY_TIME`        | Время ежедневного напоминания по умолчанию   |
| `DEFAULT_WEEKLY_DAY`        | День еженедельного напоминания по умолчанию  |
| `DEFAULT_WEEKLY_TIME`       | Время еженедельного напоминания по умолчанию |
| `DEFAULT_MONTHLY_DAY`       | День ежемесячного напоминания по умолчанию   |
| `DEFAULT_MONTHLY_TIME`      | Время ежемесячного напоминания по умолчанию  |
| `WHISPER_MODEL`             | Модель для optional speech-to-text           |
| `WHISPER_DEVICE`            | Устройство для optional speech-to-text       |
| `CELERY_BROKER_URL`         | Broker для Celery                            |
| `CELERY_RESULT_BACKEND`     | Backend результатов Celery                   |
| `LOG_LEVEL`                 | Уровень логирования                          |
| `SENTRY_DSN`                | DSN для Sentry                               |
| `SENTRY_ENVIRONMENT`        | Окружение Sentry                             |
| `SENTRY_TRACES_SAMPLE_RATE` | Доля трассировок Sentry                      |
| `OBSERVABILITY_HOST`        | Хост endpoint’а метрик                       |
| `OBSERVABILITY_PORT`        | Порт endpoint’а метрик                       |

## Release checklist

Перед публикацией релиза:

1. Обновить `CHANGELOG.md`.
2. Проверить `.env.example`.
3. Запустить локальные проверки качества.
4. Убедиться, что Docker Compose поднимает проект.
5. Создать semver-тег, например:

```bash
git tag v0.1.0
git push origin v0.1.0
```

После пуша тега release workflow публикует GitHub Release и Docker image в GHCR.

## Статус проекта

Проект находится в состоянии активного backend MVP.

Уже реализованы основные пользовательские сценарии: создание записей, настройки, напоминания, ретроспективы, экспорт, работа с голосовыми вложениями, миграции, фоновые задачи, Docker Compose, тесты и observability.

Ближайшие направления развития:

* добавить публичный demo GIF или скриншоты основных сценариев;
* расширить статистику дневника;
* улучшить сценарии ретроспектив;
* добавить больше пользовательских настроек;
* усилить типизацию оставшихся частей проекта;
* настроить регулярное обновление зависимостей через Dependabot или Renovate.
