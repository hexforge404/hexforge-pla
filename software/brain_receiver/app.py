#!/usr/bin/env python3
"""
Minimal Brain Receiver service for HexForge PLA Option A MVP.
- Listens on HTTP port 8788 by default (overridable via env BRAIN_RECEIVER_PORT).
- Validates incoming events against the shared contract in contracts/event.schema.json.
- Appends validated events to logs/events.ndjson with a UTC timestamp.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, request
from jsonschema import Draft202012Validator, ValidationError, FormatChecker
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "contracts" / "event.schema.json"
if not _SCHEMA_PATH.exists():
    raise RuntimeError(f"Event schema not found at {_SCHEMA_PATH}")

with _SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
    _EVENT_SCHEMA: Dict[str, Any] = json.load(schema_file)

_VALIDATOR = Draft202012Validator(_EVENT_SCHEMA, format_checker=FormatChecker())

# Log file lives at repo_root/logs/events.ndjson regardless of where the service runs from.
_LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "events.ndjson"
_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

_logger = app.logger
_logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
_handler = RotatingFileHandler(_LOG_PATH, maxBytes=5_000_000, backupCount=5)
_handler.setFormatter(logging.Formatter("%(message)s"))
_logger.handlers = [_handler]
_logger.propagate = False


def _get_request_id() -> str:
    incoming = request.headers.get("X-Request-ID")
    return incoming if incoming else uuid.uuid4().hex


def _build_log_entry(payload: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """Wrap payload with server-side timestamp and request correlation."""
    return {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "event": payload,
    }


def _write_event(entry: Dict[str, Any]) -> None:
    _logger.info(json.dumps(entry, separators=(",", ":")))


@app.route("/event", methods=["POST"])
def handle_event():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"ok": False, "error": "invalid_json"}), 400

    request_id = _get_request_id()

    try:
        _VALIDATOR.validate(payload)
    except ValidationError as err:
        path = "/".join([str(p) for p in err.path])
        detail = err.message if not path else f"{err.message} at {path}"
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "schema_validation_failed",
                    "details": detail,
                    "request_id": request_id,
                }
            ),
            400,
        )

    _write_event(_build_log_entry(payload, request_id))
    return jsonify({"ok": True, "request_id": request_id})


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"ok": True, "status": "ready"})


def main() -> None:
    port = int(
        os.environ.get(
            "BRAIN_RECEIVER_PORT",
            os.environ.get("PORT", "8788"),
        )
    )
    print(f"[brain_receiver] binding 0.0.0.0:{port}", flush=True)
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
