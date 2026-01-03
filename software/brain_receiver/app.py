#!/usr/bin/env python3
"""
Minimal Brain Receiver service for HexForge PLA Option A MVP.
- Listens on HTTP port 8788 by default (overridable via env BRAIN_RECEIVER_PORT).
- Validates incoming button events against a simple schema.
- Appends validated events to logs/events.ndjson with a UTC timestamp.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, request
from jsonschema import ValidationError, validate

app = Flask(__name__)

# Accepted buttons can be extended as needed without changing the payload shape.
_ALLOWED_BUTTONS = [
    "MENU",
    "OK",
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "BACK",
    "POWER",
]

EVENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["device_id", "type", "button", "state", "ts_ms"],
    "properties": {
        "device_id": {"type": "string", "minLength": 1},
        "type": {"type": "string", "const": "button_event"},
        "button": {"type": "string", "enum": _ALLOWED_BUTTONS},
        "state": {"type": "string", "enum": ["pressed", "released"]},
        "ts_ms": {"type": "integer", "minimum": 0},
    },
    "additionalProperties": False,
}

# Log file lives at repo_root/logs/events.ndjson regardless of where the service runs from.
_LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "events.ndjson"
_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _build_log_entry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap payload with a server-side timestamp for auditability."""
    return {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "event": payload,
    }


def _write_event(entry: Dict[str, Any]) -> None:
    with _LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, separators=(",", ":")) + "\n")


@app.route("/event", methods=["POST"])
def handle_event():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"ok": False, "error": "invalid_json"}), 400

    try:
        validate(instance=payload, schema=EVENT_SCHEMA)
    except ValidationError as err:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "schema_validation_failed",
                    "details": err.message,
                }
            ),
            400,
        )

    _write_event(_build_log_entry(payload))
    return jsonify({"ok": True})


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
