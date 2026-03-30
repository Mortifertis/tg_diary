from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import socket
import time
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


class _HistogramHandle:
    def __init__(
        self,
        histogram: "PrometheusHistogram",
        label_values: tuple[str, ...],
    ) -> None:
        self._histogram = histogram
        self._label_values = label_values

    def observe(self, amount: float) -> None:
        self._histogram._observe_for_labels(self._label_values, amount)


class PrometheusHistogram:
    def __init__(
        self,
        name: str,
        description: str,
        buckets: tuple[float, ...],
        label_names: tuple[str, ...] = (),
    ) -> None:
        self.name = name
        self.description = description
        self.label_names = label_names
        self.buckets = tuple(sorted(buckets))
        self._lock = Lock()
        self._values: dict[tuple[str, ...], dict[str, Any]] = {}
        if not self.label_names:
            self._values[()] = self._empty_bucket_state()

    def labels(self, **labels: str) -> _HistogramHandle:
        values = tuple(labels[key] for key in self.label_names)
        return _HistogramHandle(histogram=self, label_values=values)

    def _empty_bucket_state(self) -> dict[str, Any]:
        return {
            "count": 0.0,
            "sum": 0.0,
            "bucket_counts": [0.0 for _ in self.buckets],
        }

    def _observe_for_labels(
        self,
        label_values: tuple[str, ...],
        amount: float,
    ) -> None:
        with self._lock:
            state = self._values.get(label_values)
            if state is None:
                state = self._empty_bucket_state()
                self._values[label_values] = state
            state["count"] += 1.0
            state["sum"] += amount
            bucket_counts = state["bucket_counts"]
            for index, bucket in enumerate(self.buckets):
                if amount <= bucket:
                    bucket_counts[index] += 1.0

    def to_prometheus(self) -> str:
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} histogram",
        ]
        with self._lock:
            for label_values, state in self._values.items():
                count = float(state["count"])
                value_sum = float(state["sum"])
                bucket_counts = list(state["bucket_counts"])
                for index, bucket in enumerate(self.buckets):
                    labels = self._build_labels(
                        label_values,
                        {"le": str(bucket)},
                    )
                    lines.append(
                        f"{self.name}_bucket{{{labels}}} "
                        f"{bucket_counts[index]}"
                    )
                inf_labels = self._build_labels(
                    label_values,
                    {"le": "+Inf"},
                )
                lines.append(
                    f"{self.name}_bucket{{{inf_labels}}} {count}"
                )
                base_labels = self._build_labels(label_values, {})
                lines.append(
                    f"{self.name}_count{{{base_labels}}} {count}"
                )
                lines.append(
                    f"{self.name}_sum{{{base_labels}}} {value_sum}"
                )
        return "\n".join(lines)

    def _build_labels(
        self,
        label_values: tuple[str, ...],
        extra_labels: dict[str, str],
    ) -> str:
        labels = {
            key: value
            for key, value in zip(
                self.label_names,
                label_values,
                strict=True,
            )
        }
        labels.update(extra_labels)
        return ",".join(
            f'{key}="{value}"' for key, value in labels.items()
        )


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
    ("task", "status"),
)
EXTERNAL_API_ERRORS_TOTAL = PrometheusCounter(
    "tg_diary_external_api_errors_total",
    "Total number of external API errors",
    ("api", "operation", "error"),
)
CELERY_RETRIES_TOTAL = PrometheusCounter(
    "tg_diary_celery_retries_total",
    "Total number of Celery retries",
    ("task", "reason"),
)
ALERTS_TOTAL = PrometheusCounter(
    "tg_diary_alerts_total",
    "Total number of emitted alerts",
    ("category", "severity"),
)
PROCESSING_DURATION_SECONDS = PrometheusHistogram(
    "tg_diary_processing_duration_seconds",
    "Processing duration in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
    label_names=("component", "operation"),
)

ALL_COUNTERS = (
    BOT_STARTUPS_TOTAL,
    POLLING_EXCEPTIONS_TOTAL,
    REMINDER_TASKS_TOTAL,
    EXTERNAL_API_ERRORS_TOTAL,
    CELERY_RETRIES_TOTAL,
    ALERTS_TOTAL,
    PROCESSING_DURATION_SECONDS,
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
        alert_fields = getattr(record, "alert_fields", None)
        if alert_fields:
            payload["alert"] = alert_fields

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


def observe_duration(
    component: str,
    operation: str,
    started_at: float,
) -> None:
    elapsed = time.monotonic() - started_at
    PROCESSING_DURATION_SECONDS.labels(
        component=component,
        operation=operation,
    ).observe(elapsed)


def emit_alert(
    category: str,
    message: str,
    severity: str = "warning",
    **fields: str,
) -> None:
    ALERTS_TOTAL.labels(category=category, severity=severity).inc()
    logger = logging.getLogger("app.alerts")
    logger.warning(
        "ALERT[%s][%s] %s",
        category,
        severity,
        message,
        extra={"alert_fields": fields},
    )


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
