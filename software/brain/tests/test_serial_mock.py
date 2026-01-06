import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import BrainConfig
from esp32_client import Esp32Client


def _payload():
    ts = datetime.now(timezone.utc).isoformat()
    return {
        "execution_id": "exec_abc12345",
        "proposal_id": "prop_abc12345",
        "timestamp": ts,
        "mode": "EXECUTE",
        "action_type": "TYPE_TEXT",
        "payload": {"text": "lab hello"},
        "safety_bounds": {"max_text_length": 1024, "min_action_delay_ms": 100},
        "operator_approval": {"decision_timestamp": ts, "operator_id": "op"},
    }


def test_lab_mode_returns_ack():
    cfg = BrainConfig(lab_mode=True)
    client = Esp32Client(cfg)
    client.arm(True, physical_ok=True)
    ack = client.send_execute(_payload())
    assert ack["type"] == "ack"
    assert ack["ok"] is True
