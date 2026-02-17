from app.handlers.settings import _is_valid_time


def test_is_valid_time_accepts_hh_mm() -> None:
    assert _is_valid_time("13:38") is True


def test_is_valid_time_rejects_invalid_values() -> None:
    assert _is_valid_time("13:99") is False
    assert _is_valid_time("9:00") is False
    assert _is_valid_time("13-38") is False
