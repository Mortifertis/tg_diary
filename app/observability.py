from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import socket
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from typing import Any

PROMETHEUS_CONTENT_TYPE = (
    "text/plain; version=0.0.4; charset=utf-8"
)


class _CounterHandle:
    def __init__(
        self,
        counter: "PrometheusCounter",
        label_values: tuple[str, ...],
    ) -> None:
        self._counter = counter
        self._label_values = label_values

    def inc(self, amount: float = 1.0) -> None:
        self._counter._inc_for_labels(self._label_values, amount)


class PrometheusCounter:
    def __init__(
        self,
        name: str,
        description: str,
        label_names: tuple[str, ...] = (),
    ) -> None:
        self.name = name
        self.description = description
        self.label_names = label_names
        self._lock = Lock()
        self._values: dict[tuple[str, ...], float] = {}
        if not self.label_names:
            self._values[()] = 0.0

    def inc(self, amount: float = 1.0) -> None:
        self._inc_for_labels((), amount)

    def labels(self, **labels: str) -> _CounterHandle:
        values = tuple(labels[key] for key in self.label_names)
        return _CounterHandle(counter=self, label_values=values)

    def _inc_for_labels(
        self,
        label_values: tuple[str, ...],
        amount: float,
    ) -> None:
        with self._lock:
            current = self._values.get(label_values, 0.0)
            self._values[label_values] = current + amount

    def to_prometheus(self) -> str:
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} counter",
        ]
        with self._lock:
            for label_values, value in self._values.items():
                if self.label_names:
                    labels = ",".join(
                        f'{name}="{val}"'
                        for name, val in zip(
                            self.label_names,
                            label_values,
                            strict=True,
                        )
                    )
                    lines.append(f"{self.name}{{{labels}}} {value}")
                else:
                    lines.append(f"{self.name} {value}")

        return "\n".join(lines)


BOT_STARTUPS_TOTAL = PrometheusCounter(
    "tg_diary_bot_startups_total",
    "Total number of bot startups",
)
POLLING_EXCEPTIONS_TOTAL = PrometheusCounter(
    "tg_diary_polling_exceptions_total",
    "Total number of polling exceptions",
    ("component",),
)
REMINDER_TASKS_TOTAL = PrometheusCounter(
    "tg_diary_reminder_tasks_total",
    "Total number of reminder tasks",
    ("task",),
)

ALL_COUNTERS = (
    BOT_STARTUPS_TOTAL,
    POLLING_EXCEPTIONS_TOTAL,
    REMINDER_TASKS_TOTAL,
)


class JsonLogFormatter(logging.Formatter):
    """Format log records as JSON for easier parsing."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level_name: str = "INFO") -> None:
    """Configure root logger to emit structured JSON logs."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)


def setup_sentry(
    dsn: str,
    environment: str,
    traces_sample_rate: float,
) -> None:
    """Initialize Sentry integration when DSN is provided."""
    if not dsn:
        return

    spec = importlib.util.find_spec("sentry_sdk")
    if spec is None:
        logging.getLogger(__name__).warning(
            "Sentry DSN provided but sentry_sdk is not installed",
        )
        return

    sentry_sdk = importlib.import_module("sentry_sdk")
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
    )


class _ObservabilityHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int]) -> None:
        super().__init__(server_address, _ObservabilityHandler)
        self.allow_reuse_address = True


class _ObservabilityHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        # HTTP server access logs are omitted; app logger handles events.
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/health", "/healthz"}:
            payload = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/metrics":
            payload = render_metrics().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", PROMETHEUS_CONTENT_TYPE)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()


def render_metrics() -> str:
    metrics = [counter.to_prometheus() for counter in ALL_COUNTERS]
    return "\n".join(metrics) + "\n"


class ObservabilityServer:
    """Background HTTP server exposing health and Prometheus metrics."""

    def __init__(self, host: str, port: int) -> None:
        self._server = _ObservabilityHTTPServer((host, port))
        self._thread = Thread(target=self._server.serve_forever, daemon=True)

    @property
    def bound_port(self) -> int:
        return int(self._server.server_address[1])

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def start_observability_server(
    host: str,
    port: int,
) -> ObservabilityServer | None:
    """Start observability server if port is positive."""
    if port <= 0:
        return None

    server = ObservabilityServer(host=host, port=port)
    server.start()
    return server


def get_free_port() -> int:
    """Find an available local TCP port. Used in tests."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])
