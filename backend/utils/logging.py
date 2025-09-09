import os
import sys
import json
import uuid
import time
import logging as _logging
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler


_TRACE_ID: ContextVar[str | None] = ContextVar("trace_id", default=None)


class JsonFormatter(_logging.Formatter):
    def format(self, record: _logging.LogRecord) -> str:
        base = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)) + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "trace_id": get_trace_id(),
            "pid": os.getpid(),
            "thread": record.threadName,
            "file": record.pathname,
            "line": record.lineno,
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)


def _build_console_formatter() -> _logging.Formatter:
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s (trace_id=%(trace_id)s)"
    datefmt = "%H:%M:%S"
    return _logging.Formatter(fmt=fmt, datefmt=datefmt)


def _ensure_log_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def configure_logging(
    *,
    level: str | int | None = None,
    to_console: bool | None = None,
    json_console: bool | None = None,
    file_path: str | None = None,
    max_bytes: int | None = None,
    backup_count: int | None = None,
) -> None:
    level = (
        level
        if level is not None
        else os.getenv("LOG_LEVEL", "INFO").upper()
    )
    to_console = (
        to_console
        if to_console is not None
        else os.getenv("LOG_TO_CONSOLE", "1") in {"1", "true", "True"}
    )
    json_console = (
        json_console
        if json_console is not None
        else os.getenv("LOG_FORMAT", "json").lower() == "json"
    )
    file_path = file_path or os.getenv(
        "LOG_FILE",
        os.path.join(os.getcwd(), "logs/app.log"),
    )
    max_bytes = max_bytes or int(os.getenv("LOG_MAX_BYTES", str(5 * 1024 * 1024)))
    backup_count = backup_count or int(os.getenv("LOG_BACKUP_COUNT", "5"))

    root = _logging.getLogger()
    root.setLevel(level)

    for h in list(root.handlers):
        root.removeHandler(h)

    if to_console:
        console = _logging.StreamHandler(stream=sys.stdout)
        if json_console:
            console.setFormatter(JsonFormatter())
        else:
            console.setFormatter(_build_console_formatter())
        console.addFilter(_TraceIdFilter())
        root.addHandler(console)

    if file_path:
        _ensure_log_dir(file_path)
        file_handler = RotatingFileHandler(file_path, maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setFormatter(JsonFormatter())
        file_handler.addFilter(_TraceIdFilter())
        root.addHandler(file_handler)


class _TraceIdFilter(_logging.Filter):
    def filter(self, record: _logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        return True


def get_logger(name: str | None = None) -> _logging.Logger:
    return _logging.getLogger(name)


def new_trace_id() -> str:
    return uuid.uuid4().hex


def set_trace_id(trace_id: str | None) -> None:
    _TRACE_ID.set(trace_id)


def get_trace_id() -> str | None:
    return _TRACE_ID.get()


