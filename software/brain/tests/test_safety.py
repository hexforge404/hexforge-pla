import sys
from pathlib import Path
from datetime import datetime, timezone
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import BrainConfig
from mode_manager import ModeManager
from esp32_client import Esp32Client


def _exec_payload(text: str = "hello"):
    ts = datetime.now(timezone.utc).isoformat()
    return {
        "execution_id": "exec_12345678",
        "proposal_id": "prop_12345678",
        "timestamp": ts,
        "mode": "EXECUTE",
        "action_type": "TYPE_TEXT",
        "payload": {"text": text},
        "safety_bounds": {"max_text_length": 1024, "min_action_delay_ms": 100},
        "operator_approval": {"decision_timestamp": ts, "operator_id": "op"},
    }


def test_mode_gating_blocks_execute():
    modes = ModeManager()
    assert modes.can_execute is False
    with pytest.raises(PermissionError):
        modes.require_execute()
    modes.set_mode("EXECUTE")
    assert modes.can_execute is True


def test_executor_requires_arm_and_bounds():
    cfg = BrainConfig(lab_mode=True)
    client = Esp32Client(cfg)
    payload = _exec_payload()
    with pytest.raises(PermissionError):
        client.send_execute(payload)
    client.arm(True, physical_ok=True)
    with pytest.raises(ValueError):
        client.send_execute(_exec_payload(text="x" * (cfg.serial.max_text + 1)))


def test_executor_rate_limit():
    cfg = BrainConfig(lab_mode=True)
    client = Esp32Client(cfg)
    client.arm(True, physical_ok=True)
    payload = _exec_payload()
    client.send_execute(payload)
    with pytest.raises(RuntimeError):
        client.send_execute(payload)
