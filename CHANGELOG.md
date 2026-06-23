# Changelog

## Unreleased

- Reworked project presentation materials for portfolio review.
- Moved test and voice-recognition dependencies out of runtime requirements.
- Added explicit migration command and disabled automatic startup migrations by
  default.
- Replaced Bot monkey-patching with an application-level DB session factory.

## v0.1.0 - 2026-06-23

- MVP Telegram diary bot with entries, reminders, settings, exports,
  localization, Celery tasks, Alembic migrations, observability and tests.