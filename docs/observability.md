# Observability

`tg_diary` содержит lightweight observability primitives, которых достаточно
для local runs, Docker Compose и небольших self-hosted deployments.

## Health endpoints

Bot-процесс запускает background HTTP server, если `OBSERVABILITY_PORT` больше
нуля.

| Endpoint | Response | Назначение |
| --- | --- | --- |
| `/health` | JSON `status: ok` | Basic liveness check. |
| `/healthz` | JSON `status: ok` | Alias для liveness checks. |
| `/metrics` | Prometheus text format | Runtime counters и histograms. |

Настройки bind по умолчанию:

```env
OBSERVABILITY_HOST=0.0.0.0
OBSERVABILITY_PORT=8001
```

Чтобы отключить server, задайте `OBSERVABILITY_PORT=0`.

## Metrics

Endpoint `/metrics` отдаёт Prometheus-compatible text. Текущие metric families:

| Metric | Type | Labels | Meaning |
| --- | --- | --- | --- |
| `tg_diary_bot_startups_total` | Counter | none | Количество startup bot process. |
| `tg_diary_polling_exceptions_total` | Counter | `component` | Unexpected polling failures. |
| `tg_diary_reminder_tasks_total` | Counter | `task`, `status` | Success/error reminder tasks. |
| `tg_diary_external_api_errors_total` | Counter | `api`, `operation`, `error` | External API failures. |
| `tg_diary_celery_retries_total` | Counter | `task`, `reason` | Celery retry attempts. |
| `tg_diary_alerts_total` | Counter | `category`, `severity` | Application alerts. |
| `tg_diary_processing_duration_seconds` | Histogram | `component`, `operation` | Processing duration buckets. |

## Sentry

Sentry опционален и инициализируется только при непустом `SENTRY_DSN`.

```env
SENTRY_DSN=
SENTRY_ENVIRONMENT=dev
SENTRY_TRACES_SAMPLE_RATE=0.0
```

Если DSN задан, но `sentry_sdk` недоступен, application пишет warning в logs и
продолжает работу.

## JSON logs

Application logs пишутся в stdout в формате JSON. Каждая запись содержит:

* `timestamp`
* `level`
* `logger`
* `message`
* `exception`, если есть exception information
* `alert`, если запись создана через alert helper

Такой формат удобен для Docker logs, log collectors и managed container
platforms.

## Recommended checks

Local health check:

```bash
curl http://127.0.0.1:8001/health
```

Local metrics check:

```bash
curl http://127.0.0.1:8001/metrics
```

В Docker нужно expose или proxy observability port перед scraping извне Compose
network.