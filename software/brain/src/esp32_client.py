"""ESP32 HID executor client with lab-mode stub."""

from __future__ import annotations

import json
import time
from typing import Dict, Any, Optional

from config import BrainConfig
from contract_validator import validate_execute, validate_device_status

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover
    serial = None


class Esp32Client:
    def __init__(self, cfg: BrainConfig):
        self.cfg = cfg
        self._ser = None
        self._armed = False
        self._physical_ok = False
        self._last_status: Optional[Dict[str, Any]] = None
        self._last_send = 0.0
        self._last_status_ts = time.monotonic() if cfg.lab_mode else 0.0
        if not cfg.lab_mode and serial is not None:
            self._ser = serial.Serial(cfg.serial.port, cfg.serial.baudrate, timeout=cfg.serial.timeout)

    def arm(self, enabled: bool, physical_ok: bool = True) -> None:
        self._physical_ok = physical_ok
        if enabled and not physical_ok and self.cfg.require_physical_arm:
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
            self._last_status_ts = time.monotonic()
        if not self.cfg.lab_mode and now - self._last_status_ts > self.cfg.serial.status_heartbeat_s * 2:
            raise ConnectionError("stale executor heartbeat")
        if not self._armed:
            raise PermissionError("executor not armed")
        if self.cfg.require_physical_arm and not self._physical_ok:
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
                "event_type": "device_status",
                "device_id": "esp32-lab",
                "mode": "EXECUTE" if self._armed else "SUGGEST",
                "led_state": self._armed,
                "kill_switch_state": self._armed,
                "ts": int(time.time()),
            }
            ok, err = validate_device_status(status)
            if ok:
                self._physical_ok = status["kill_switch_state"]
                self._last_status = status
                self._last_status_ts = time.monotonic()
                return status
            return None
        if self._ser is None or self._ser.in_waiting == 0:
            return self._last_status
        line = self._ser.readline().decode("utf-8", errors="ignore").strip()
        try:
            status = json.loads(line)
        except Exception:
            return self._last_status
        ok, _ = validate_device_status(status)
        if ok:
            self._last_status = status
            self._physical_ok = bool(status.get("kill_switch_state"))
            self._last_status_ts = time.monotonic()
            return status
        return self._last_status

    def close(self) -> None:
        if self._ser is not None:
            self._ser.close()
            self._ser = None
