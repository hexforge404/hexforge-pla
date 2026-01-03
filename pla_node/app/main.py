"""
PLA Node: production gateway for PLA events.
- Flask + optional API key gate (PLA_API_KEY)
- Validate events against contracts/event.schema.json and enforce event_version
- Forward to Brain Receiver (http://127.0.0.1:8788/event); spool + retry on failure
- NDJSON logging for observability
"""
from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

import requests
from flask import Flask, jsonify, request
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

APP_VERSION = "0.2.0"
BRAIN_RECEIVER_URL = "http://127.0.0.1:8788/event"
PORT = int(os.getenv("PLA_NODE_PORT", "8787"))

API_KEY = os.getenv("PLA_API_KEY")  # Optional; if set, required for calls
EVENT_VERSION = os.getenv("PLA_EVENT_VERSION", "1.0")

SCHEMA_PATH = Path(__file__).resolve().parents[1].parent / "contracts" / "event.schema.json"
if not SCHEMA_PATH.exists():
    raise RuntimeError(f"Event schema not found at {SCHEMA_PATH}")

with SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
    EVENT_SCHEMA: Dict[str, Any] = json.load(schema_file)

VALIDATOR = Draft202012Validator(EVENT_SCHEMA, format_checker=FormatChecker())

SPOOL_DIR = Path(__file__).resolve().parent.parent / "spool"
SPOOL_DIR.mkdir(parents=True, exist_ok=True)

start_monotonic = time.monotonic()

metrics: Dict[str, Any] = {
    "last_ingest_ts": None,
    "last_forward_success_ts": None,
    "last_forward_failure_ts": None,
    "forward_success_count": 0,
    "forward_failure_count": 0,
}

spool_lock = threading.Lock()

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = REPO_ROOT / "logs" / "events.ndjson"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("pla_node")
logger.setLevel(logging.INFO)
_file_handler = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=5)
_file_handler.setFormatter(logging.Formatter("%(message)s"))
logger.handlers = [_file_handler]
logger.propagate = False

app = Flask(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _spool_queue_depth() -> int:
    return len(list(SPOOL_DIR.glob("*.ndjson")))


def _event_id(payload: Dict[str, Any]) -> str:
    device_id = payload.get("device_id", "unknown")
    seq = payload.get("seq")
    return f"{device_id}:{seq}" if seq is not None else str(device_id)


def _request_id(payload: Dict[str, Any]) -> str:
    header_rid = request.headers.get("X-Request-ID") if request else None
    if header_rid:
        return header_rid
    return payload.get("request_id") or str(uuid4())


def log_json(message: str, **extra: Any) -> None:
    entry = {"ts": _now_iso(), "msg": message}
    entry.update(extra)
    logger.info(json.dumps(entry, separators=(",", ":")))


def _require_api_key():
    if request.path == "/health":
        return None
    if API_KEY:
        provided = request.headers.get("X-API-Key")
        if provided != API_KEY:
            return jsonify({"ok": False, "error": "unauthorized"}), 401
    return None


def _validate_event(payload: Dict[str, Any]) -> None:
    VALIDATOR.validate(payload)
    if payload.get("event_version") != EVENT_VERSION:
        raise ValidationError(f"event_version must be '{EVENT_VERSION}'")


def _write_spool(payload: Dict[str, Any]) -> None:
    filename = f"event-{int(time.time()*1000)}-{threading.get_ident()}.ndjson"
    path = SPOOL_DIR / filename
    with spool_lock:
        with path.open("w", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, separators=(",", ":")) + "\n")


def _forward_event(payload: Dict[str, Any], timeout: float = 3.0) -> None:
    rid = _request_id(payload)
    resp = requests.post(
        BRAIN_RECEIVER_URL,
        json=payload,
        headers={"X-Request-ID": rid},
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"forward failed status={resp.status_code}")


def _forward_or_spool(payload: Dict[str, Any]) -> None:
    event_id = _event_id(payload)
    rid = _request_id(payload)
    try:
        _forward_event(payload)
        metrics["forward_success_count"] += 1
        metrics["last_forward_success_ts"] = _now_iso()
        log_json("forward_success", event_id=event_id, event_type=payload.get("event_type"), request_id=rid)
    except Exception as exc:  # noqa: BLE001
        metrics["forward_failure_count"] += 1
        metrics["last_forward_failure_ts"] = _now_iso()
        _write_spool(payload)
        log_json(
            "forward_failed_spooled",
            event_id=event_id,
            event_type=payload.get("event_type"),
            request_id=rid,
            error=str(exc),
        )


def _process_spool_loop() -> None:
    while True:
        files = sorted(SPOOL_DIR.glob("*.ndjson"))
        if not files:
            time.sleep(3)
            continue
        for path in files:
            try:
                with path.open("r", encoding="utf-8") as fp:
                    line = fp.readline()
                    payload = json.loads(line)
                rid = _request_id(payload)
                _forward_event(payload)
                metrics["forward_success_count"] += 1
                metrics["last_forward_success_ts"] = _now_iso()
                log_json(
                    "retry_forward_success",
                    event_id=_event_id(payload),
                    event_type=payload.get("event_type"),
                    request_id=rid,
                )
                path.unlink(missing_ok=True)
            except Exception as exc:  # noqa: BLE001
                metrics["forward_failure_count"] += 1
                metrics["last_forward_failure_ts"] = _now_iso()
                log_json("retry_forward_failed", error=str(exc))
                time.sleep(2)
                break


auth_guard = app.before_request(_require_api_key)
retry_thread = threading.Thread(target=_process_spool_loop, daemon=True)
retry_thread.start()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "status": "ready"})


@app.route("/ingest", methods=["POST"])
def ingest():
    metrics["last_ingest_ts"] = _now_iso()
    payload = request.get_json(silent=True)
    if payload is None:
        log_json("ingest_invalid_json")
        return jsonify({"ok": False, "error": "invalid_json"}), 400
    try:
        _validate_event(payload)
    except ValidationError as err:
        path = "/".join([str(p) for p in err.path])
        detail = err.message if not path else f"{err.message} at {path}"
        log_json("ingest_schema_failed", details=detail)
        return jsonify({"ok": False, "error": "schema_validation_failed", "details": detail}), 400

    rid = _request_id(payload)
    log_json("ingest_accepted", event_id=_event_id(payload), event_type=payload.get("event_type"), request_id=rid)
    threading.Thread(target=_forward_or_spool, args=(payload,), daemon=True).start()


@app.route("/metrics", methods=["GET"])
    return jsonify({"ok": True, "accepted": True}), 202
    uptime_seconds = int(time.monotonic() - start_monotonic)
    lines = [
        f"pla_node_uptime_seconds {uptime_seconds}",
        f"pla_node_forward_success_total {metrics['forward_success_count']}",
        f"pla_node_forward_failure_total {metrics['forward_failure_count']}",
        f"pla_node_spool_queue_depth {_spool_queue_depth()}",
    ]
    return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; version=0.0.4"}


@app.route("/status", methods=["GET"])
def status():
    uptime_seconds = int(time.monotonic() - start_monotonic)
    return jsonify(
        {
            "service": "pla_node",
            "version": APP_VERSION,
            "ok": True,
            "uptime_seconds": uptime_seconds,
            "last_ingest_ts": metrics["last_ingest_ts"],
            "last_forward_success_ts": metrics["last_forward_success_ts"],
            "last_forward_failure_ts": metrics["last_forward_failure_ts"],
            "forward_success_count": metrics["forward_success_count"],
            "forward_failure_count": metrics["forward_failure_count"],
            "spool_queue_depth": _spool_queue_depth(),
            "retry_active": retry_thread.is_alive(),
        }
    )


def main() -> None:
    log_json("pla_node_start", version=APP_VERSION, port=PORT)
    app.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
