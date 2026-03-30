from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter

import pytest

from app.i18n import menu_variants, tr
from app.services.timezones import local_datetime_for_user


@dataclass
class _UserStub:
    timezone: str | None


@pytest.mark.performance
def test_i18n_translation_lookup_performance() -> None:
    started = perf_counter()
    for _ in range(15000):
        assert tr("ru", "menu_settings") == "Настройки"
    elapsed = perf_counter() - started

    assert elapsed < 1.5


@pytest.mark.performance
def test_menu_variants_performance() -> None:
    started = perf_counter()
    expected = {"Настройки", "Settings", "Paramètres", "Einstellungen"}
    for _ in range(3000):
        assert menu_variants("menu_settings") == expected
    elapsed = perf_counter() - started

    assert elapsed < 1.5


@pytest.mark.performance
def test_timezone_conversion_regression_budget() -> None:
    user = _UserStub(timezone="Europe/Berlin")
    value = datetime(2026, 3, 30, 18, 45, tzinfo=UTC)

    started = perf_counter()
    for _ in range(10000):
        converted = local_datetime_for_user(user, value)
        assert converted.tzinfo is not None
    elapsed = perf_counter() - started

    assert elapsed < 1.5
