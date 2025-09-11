import json
import os
import sys
import time
from typing import Any, Dict, Optional
from decimal import Decimal


SERVICE_NAME = os.getenv("SERVICE_NAME", "gold-prices-fetcher")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()
LOG_DEST = os.getenv("LOG_DEST", "stdout").lower()  # stdout | file
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/app.log")

def _now_unix_ms() -> int:
    return int(time.time() * 1000)


def _level_to_int(level: str) -> int:
    mapping = {
        "debug": 10,
        "info": 20,
        "warning": 30,
        "error": 40,
        "critical": 50,
    }
    return mapping.get(level.lower(), 20)


def _write(line: str) -> None:
    if LOG_DEST == "stdout":
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
    else:
        # write to file
        directory = os.path.dirname(LOG_FILE_PATH) or "."
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception:
            # fallback to stdout if cannot create directory
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
            return
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def _json_default(obj: Any):
    if isinstance(obj, Decimal):
        return float(obj)
    try:
        return str(obj)
    except Exception:
        return repr(obj)


def log(level: str, message: str, *, trace_id: Optional[str] = None, **fields: Any) -> None:
    record: Dict[str, Any] = {
        "ts": _now_unix_ms(),
        "level": level.lower(),
        "level_int": _level_to_int(level),
        "msg": message,
        "service": SERVICE_NAME,
    }
    if trace_id:
        record["trace_id"] = trace_id
    if fields:
        record.update(fields)
    # level filter
    if record["level_int"] >= _level_to_int(LOG_LEVEL):
        _write(json.dumps(record, separators=(",", ":"), default=_json_default))


def info(message: str, *, trace_id: Optional[str] = None, **fields: Any) -> None:
    log("info", message, trace_id=trace_id, **fields)


def error(message: str, *, trace_id: Optional[str] = None, **fields: Any) -> None:
    log("error", message, trace_id=trace_id, **fields)


def debug(message: str, *, trace_id: Optional[str] = None, **fields: Any) -> None:
    log("debug", message, trace_id=trace_id, **fields)


def warning(message: str, *, trace_id: Optional[str] = None, **fields: Any) -> None:
    log("warning", message, trace_id=trace_id, **fields)


