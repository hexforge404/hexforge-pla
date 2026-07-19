import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import esp32_client as esp32_module
from config import BrainConfig
from contract_validator import validate_device_status
from esp32_client import Esp32Client, is_exact_armed


def _status(kill_state="ARMED", **updates):
    status = {
        "device_id": "esp32-test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "EXECUTE",
        "led_state": True,
        "kill_switch_state": kill_state,
        "uptime_seconds": 1,
    }
    status.update(updates)
    return status


def _payload():
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "execution_id": "exec_abc12345",
        "proposal_id": "prop_abc12345",
        "timestamp": timestamp,
        "mode": "EXECUTE",
        "action_type": "TYPE_TEXT",
        "payload": {"text": "inert mock"},
        "safety_bounds": {"max_text_length": 1024, "min_action_delay_ms": 100},
        "operator_approval": {"decision_timestamp": timestamp, "operator_id": "op"},
    }


class FakeSerial:
    def __init__(self, lines=()):
        self.lines = [line.encode("utf-8") for line in lines]
        self.writes = []
        self.closed = False

    @property
    def in_waiting(self):
        return len(self.lines)

    def readline(self):
        return self.lines.pop(0) if self.lines else b""

    def write(self, payload):
        self.writes.append(payload)

    def close(self):
        self.closed = True


def _serial_client(monkeypatch, lines=()):
    fake = FakeSerial(lines)
    monkeypatch.setattr(esp32_module, "serial", SimpleNamespace(Serial=lambda *args, **kwargs: fake))
    client = Esp32Client(BrainConfig(lab_mode=False, require_physical_arm=True))
    return client, fake


@pytest.mark.parametrize(
    "value,expected",
    [
        ("ARMED", True),
        ("DISABLED", False),
        ("UNKNOWN", False),
        ("armed", False),
        ("Armed", False),
        (" ARMED", False),
        ("ARMED ", False),
        ("\tARMED", False),
        ("ARMED\n", False),
        ("", False),
        (None, False),
        (True, False),
        (False, False),
        (0, False),
        (1, False),
        (-17, False),
        (1.5, False),
        ([], False),
        ({}, False),
        ({"state": "ARMED"}, False),
        ("SAFE", False),
        ("ON", False),
        ("1", False),
        ("arbitrary", False),
    ],
)
def test_only_exact_armed_is_safe(value, expected):
    assert is_exact_armed(value) is expected


@pytest.mark.parametrize("valid_value", ["ARMED", "DISABLED", "UNKNOWN"])
def test_authoritative_enum_values_validate(valid_value):
    valid, error = validate_device_status(_status(valid_value))
    assert valid, error


@pytest.mark.parametrize(
    "invalid_value",
    [
        "armed", "Armed", " ARMED", "ARMED ", "", None, True, False,
        0, 1, -1, 1.5, [], {}, "SAFE", "ON", "1", "arbitrary",
    ],
)
def test_malformed_and_coercion_values_fail_schema(invalid_value):
    valid, _ = validate_device_status(_status(invalid_value))
    assert valid is False


def test_missing_kill_state_fails_schema():
    status = _status()
    del status["kill_switch_state"]
    valid, _ = validate_device_status(status)
    assert valid is False


def test_lab_mode_emits_canonical_armed_string():
    client = Esp32Client(BrainConfig(lab_mode=True))
    status = client.read_status()
    assert status["kill_switch_state"] == "ARMED"
    assert type(status["kill_switch_state"]) is str
    assert client.physical_safe is True


@pytest.mark.parametrize("kill_state", ["DISABLED", "UNKNOWN"])
def test_valid_nonarmed_state_blocks_action(monkeypatch, kill_state):
    client, fake = _serial_client(monkeypatch, [json.dumps(_status(kill_state))])
    client.read_status()
    client._armed = True
    with pytest.raises(PermissionError):
        client.send_execute(_payload())
    assert fake.writes == []


def test_mocked_serial_exact_armed_allows_action(monkeypatch):
    client, fake = _serial_client(monkeypatch, [json.dumps(_status("ARMED"))])
    client.read_status()
    client._armed = True
    response = client.send_execute(_payload())
    assert response["type"] == "err"
    assert response["message"] == "no_response"
    assert len(fake.writes) == 3


@pytest.mark.parametrize(
    "raw",
    [
        "not json\n",
        "null\n",
        "[]\n",
        "true\n",
        '{"kill_switch_state":"ARMED","kill_switch_state":"DISABLED"}\n',
    ],
)
def test_malformed_or_contradictory_serial_clears_prior_safe_state(monkeypatch, raw):
    client, fake = _serial_client(monkeypatch, [json.dumps(_status("ARMED")), raw])
    assert client.read_status()["kill_switch_state"] == "ARMED"
    assert client.physical_safe is True
    fake.lines.append(raw.encode("utf-8")) if not fake.lines else None
    client.read_status()
    assert client._physical_ok is False
    assert client.physical_safe is False


def test_schema_validation_failure_clears_prior_safe_state(monkeypatch):
    client, _ = _serial_client(
        monkeypatch,
        [json.dumps(_status("ARMED")), json.dumps(_status("armed"))],
    )
    client.read_status()
    assert client.physical_safe is True
    client.read_status()
    assert client.physical_safe is False


def test_missing_state_and_unsupported_version_block(monkeypatch):
    missing = _status()
    del missing["kill_switch_state"]
    unsupported = _status(schema_version="v999")
    client, _ = _serial_client(monkeypatch, [json.dumps(missing), json.dumps(unsupported)])
    assert client.read_status() is None
    assert client.physical_safe is False
    assert client.read_status() is None
    assert client.physical_safe is False


def test_disconnected_serial_clears_prior_safe_state(monkeypatch):
    client, _ = _serial_client(monkeypatch, [json.dumps(_status("ARMED"))])
    client.read_status()
    assert client.physical_safe is True
    client._ser = None
    client.read_status()
    assert client.physical_safe is False


def test_initial_and_repeated_no_data_never_become_safe(monkeypatch):
    client, _ = _serial_client(monkeypatch)
    assert client.read_status() is None
    assert client.physical_safe is False
    assert client.read_status() is None
    assert client.physical_safe is False


def test_stale_status_blocks_action(monkeypatch):
    client, fake = _serial_client(monkeypatch, [json.dumps(_status("ARMED"))])
    client.read_status()
    client._armed = True
    client._last_status_ts = time.monotonic() - client.cfg.serial.status_heartbeat_s * 3
    with pytest.raises(ConnectionError):
        client.send_execute(_payload())
    assert client._physical_ok is False
    assert fake.writes == []


def test_recovery_requires_new_fresh_exact_armed(monkeypatch):
    client, _ = _serial_client(
        monkeypatch,
        [json.dumps(_status("ARMED")), "bad json\n", json.dumps(_status("ARMED"))],
    )
    client.read_status()
    assert client.physical_safe is True
    client.read_status()
    assert client.physical_safe is False
    client.read_status()
    assert client.physical_safe is True
