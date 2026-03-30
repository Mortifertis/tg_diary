from __future__ import annotations

import json
import logging
from urllib.request import urlopen

from app.observability import (JsonLogFormatter, get_free_port,
                               start_observability_server)


def test_json_log_formatter_includes_required_fields() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "hello world"
    assert payload["timestamp"]


def test_observability_server_health_and_metrics() -> None:
    port = get_free_port()
    server = start_observability_server(host="127.0.0.1", port=port)

    assert server is not None

    try:
        with urlopen(f"http://127.0.0.1:{port}/health") as response:
            body = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert body == {"status": "ok"}

        with urlopen(f"http://127.0.0.1:{port}/metrics") as response:
            payload = response.read().decode("utf-8")
            assert response.status == 200
            assert "tg_diary_bot_startups_total" in payload
    finally:
        server.stop()
