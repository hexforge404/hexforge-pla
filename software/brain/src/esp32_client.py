"""ESP32 HID executor client with lab-mode stub."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from config import BrainConfig
from contract_validator import validate_execute, validate_device_status

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover
    serial = None


KILL_SWITCH_ARMED = "ARMED"
KILL_SWITCH_DISABLED = "DISABLED"
KILL_SWITCH_UNKNOWN = "UNKNOWN"


def is_exact_armed(value: Any) -> bool:
    """Return safe true only for the canonical wire value and exact string type."""
    return type(value) is str and value == KILL_SWITCH_ARMED


def _load_unique_json_object(line: str) -> Optional[Dict[str, Any]]:
    """Parse one status object while rejecting duplicate/contradictory keys."""

    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    try:
        parsed = json.loads(line, object_pairs_hook=reject_duplicates)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return parsed if type(parsed) is dict else None


class Esp32Client:
    def __init__(self, cfg: BrainConfig):
        self.cfg = cfg
        self._ser = None
        self._armed = False
        self._physical_ok = False
        self._last_status: Optional[Dict[str, Any]] = None
        self._last_send = 0.0
        self._last_status_ts = 0.0
        if not cfg.lab_mode and serial is not None:
            self._ser = serial.Serial(cfg.serial.port, cfg.serial.baudrate, timeout=cfg.serial.timeout)

    def _clear_physical_state(self) -> None:
        self._physical_ok = False
        self._last_status_ts = 0.0

    def _status_is_fresh(self, now: Optional[float] = None) -> bool:
        if self._last_status_ts <= 0.0 or type(self._last_status) is not dict:
            return False
        observed_at = time.monotonic() if now is None else now
        return observed_at - self._last_status_ts <= self.cfg.serial.status_heartbeat_s * 2

    @property
    def physical_safe(self) -> bool:
        safe = (
            self._status_is_fresh()
            and type(self._last_status) is dict
            and is_exact_armed(self._last_status.get("kill_switch_state"))
        )
        if not safe:
            self._clear_physical_state()
        return safe

    def arm(self, enabled: bool, physical_ok: Any = None) -> None:
        # The legacy physical_ok argument is intentionally ignored. Physical
        # safety is derived only from a fresh, validated device observation.
        del physical_ok
        if type(enabled) is not bool:
            raise ValueError("enabled must be a boolean")
        self.read_status()
        self._armed = False
        if enabled and self.cfg.require_physical_arm and not self.physical_safe:
            raise PermissionError("physical arm switch is OFF")
        self._armed = enabled

    def _check_rate_limit(self) -> None:
        now = time.monotonic()
        if now - self._last_send < self.cfg.serial.min_delay_s:
            raise RuntimeError("command rate-limited")

    def _write_and_read(self, payload: str) -> Dict[str, Any]:
        attempts = 3
        for attempt in range(attempts):
            self._ser.write(payload.encode("utf-8"))
            line = self._ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except Exception:
                return {"type": "err", "message": "invalid_json_from_device"}
        return {"type": "err", "message": "no_response"}

    def send_execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = time.monotonic()
        self._check_rate_limit()
        if self.cfg.lab_mode:
            self.read_status()
        if not self._armed:
            raise PermissionError("executor not armed")
        if self.cfg.require_physical_arm:
            if not self._status_is_fresh(now):
                self._clear_physical_state()
                raise ConnectionError("stale executor heartbeat")
            if not self.physical_safe:
                raise PermissionError("physical arm not confirmed")
        act_type = payload.get("action_type", "")
        inner = payload.get("payload", {})
        if act_type == "TYPE_TEXT":
            text = inner.get("text", "")
            if len(text) > self.cfg.serial.max_text:
                raise ValueError("execute text exceeds bounds")
        if act_type == "KEY_COMBO":
            keys = [str(k).lower() for k in inner.get("keys", [])]
            if not keys or any(k not in self.cfg.serial.allowed_keys for k in keys):
                raise ValueError("execute keys not allowed")
            payload["payload"]["keys"] = keys
        ok, err = validate_execute(payload)
        if not ok:
            raise ValueError(f"execute contract invalid: {err}")
        if self.cfg.lab_mode or self._ser is None:
            self._last_send = now
            return {"type": "ack", "execution_id": payload.get("execution_id", "stub"), "ok": True}
        msg = json.dumps(payload) + "\n"
        self._last_send = now
        return self._write_and_read(msg)

    def read_status(self) -> Optional[Dict[str, Any]]:
        if self.cfg.lab_mode:
            status = {
                "device_id": "esp32-lab",
                "mode": "EXECUTE" if self._armed else "SUGGEST",
                "led_state": self._armed,
                "kill_switch_state": KILL_SWITCH_ARMED,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": int(time.monotonic()),
            }
            return self._apply_device_status(status)
        if self._ser is None:
            self._clear_physical_state()
            return self._last_status
        if self._ser.in_waiting == 0:
            if not self._status_is_fresh():
                self._clear_physical_state()
            return self._last_status
        line = self._ser.readline().decode("utf-8", errors="ignore").strip()
        status = _load_unique_json_object(line)
        if status is None:
            self._clear_physical_state()
            return self._last_status
        return self._apply_device_status(status)

    def _apply_device_status(self, status: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        self._clear_physical_state()
        if type(status) is not dict or "schema_version" in status:
            return self._last_status
        ok, _ = validate_device_status(status)
        if not ok:
            return self._last_status
        self._last_status = status
        self._last_status_ts = time.monotonic()
        self._physical_ok = is_exact_armed(status.get("kill_switch_state"))
        return status

    def close(self) -> None:
        if self._ser is not None:
            self._ser.close()
            self._ser = None
