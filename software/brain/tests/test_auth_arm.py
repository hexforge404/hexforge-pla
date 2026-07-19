import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import BrainConfig
from web_ui.app import build_app
from esp32_client import Esp32Client


def _client(tmp_path):
    cfg = BrainConfig(
        lab_mode=True,
        operator_token="secret-token",
        require_physical_arm=True,
        log_dir=tmp_path,
        session_log_path=tmp_path / "session.log",
    )
    app = build_app(cfg)
    return app, cfg


def _route(app, path, method):
    return next(
        route
        for route in app.routes
        if getattr(route, "path", None) == path and method in getattr(route, "methods", set())
    )


def test_auth_required_for_mutations(tmp_path):
    app, _ = _client(tmp_path)
    dependency = _route(app, "/mode", "POST").dependant.dependencies[0].call
    with pytest.raises(HTTPException) as exc_info:
        dependency(None)
    assert exc_info.value.status_code == 401


def test_arm_and_execute_flow(tmp_path):
    app, _ = _client(tmp_path)
    set_mode = _route(app, "/mode", "POST").endpoint
    propose = _route(app, "/propose", "POST").endpoint
    arm = _route(app, "/arm", "POST").endpoint
    decide = _route(app, "/decide", "POST").endpoint

    # Move to SUGGEST and propose.
    assert set_mode({"mode": "SUGGEST"}, None)["mode"] == "SUGGEST"
    assert propose({"text": "hi"}, None)["payload"]["type"] == "TYPE_TEXT"

    # Decision without arm should fail.
    with pytest.raises(HTTPException) as exc_info:
        decide({"approved": True}, None)
    assert exc_info.value.status_code == 403

    # Request-supplied physical_ok is ignored; the canonical lab device
    # observation independently reports the protective mechanism ARMED.
    arm_response = arm({"enabled": True, "physical_ok": False}, None)
    assert arm_response["armed"] is True
    assert arm_response["physical_ok"] is True
    assert set_mode({"mode": "EXECUTE"}, None)["mode"] == "EXECUTE"

    # Now decision should execute.
    decision = decide({"approved": True}, None)
    assert decision.get("ack", {}).get("ok") is True


def test_arm_request_cannot_assert_device_physical_safety(monkeypatch, tmp_path):
    def observe_unknown(self):
        status = {
            "device_id": "esp32-lab",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "SUGGEST",
            "led_state": False,
            "kill_switch_state": "UNKNOWN",
            "uptime_seconds": int(time.monotonic()),
        }
        return self._apply_device_status(status)

    monkeypatch.setattr(Esp32Client, "read_status", observe_unknown)
    app, _ = _client(tmp_path)
    arm = _route(app, "/arm", "POST").endpoint
    with pytest.raises(HTTPException) as exc_info:
        arm({"enabled": True, "physical_ok": True}, None)
    assert exc_info.value.status_code == 403


def test_status_reports_unknown_without_granting_authority(monkeypatch, tmp_path):
    def observe_unknown(self):
        status = {
            "device_id": "esp32-lab",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "SUGGEST",
            "led_state": False,
            "kill_switch_state": "UNKNOWN",
            "uptime_seconds": int(time.monotonic()),
        }
        return self._apply_device_status(status)

    monkeypatch.setattr(Esp32Client, "read_status", observe_unknown)
    app, _ = _client(tmp_path)
    get_status = _route(app, "/status", "GET").endpoint
    result = get_status()
    assert result["device_status"]["kill_switch_state"] == "UNKNOWN"
    assert result["physical_ok"] is False


def test_arm_rejects_enabled_truthiness_coercion(tmp_path):
    app, _ = _client(tmp_path)
    arm = _route(app, "/arm", "POST").endpoint
    for value in (1, "true", "ARMED", [], {}):
        with pytest.raises(HTTPException) as exc_info:
            arm({"enabled": value}, None)
        assert exc_info.value.status_code == 400
