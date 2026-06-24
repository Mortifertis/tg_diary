# Roadmap

Этот roadmap фиксирует вероятные следующие шаги после текущего project
baseline.

## Web admin

Добавить небольшой authenticated admin interface для operational задач:

* user lookup и support diagnostics;
* просмотр reminder state;
* управление backup и export;
* read-only health dashboards.

## Encrypted exports

Усилить privacy для exported diary archives:

* password-protected archive exports;
* per-user encryption keys;
* documented restore flow;
* более безопасная работа с temporary files при генерации archives.

## Better scheduling

Сделать reminders гибче и надёжнее:

* per-user quiet hours;
* holiday и vacation pauses;
* richer recurrence rules;
* более понятные retry и dead-letter handling для delivery failures.

## Deployment guide

Добавить production deployment guide:

* использование GHCR image;
* reverse proxy и health checks;
* provisioning для PostgreSQL и Redis;
* secrets management;
* backup и restore drills;
* release workflow и rollback steps.

## Typed config

Усилить работу с configuration:

* более строгий parsing и validation для URLs, time zones и времени;
* config documentation, сгенерированная из typed fields;
* более безопасные production defaults;
* понятная startup diagnostics для invalid settings.

## Async DB

Оценить переход persistence на SQLAlchemy async sessions:

* не блокировать event loop в bot handlers;
* сохранить Celery compatibility через отдельные sync или async task patterns;
* обновить tests и migration utilities;
* измерить performance до и после migration.