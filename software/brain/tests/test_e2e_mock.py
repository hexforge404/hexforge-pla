import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import BrainConfig
from camera import CameraCapture
from ocr import OCREngine
from ai_engine import AIEngine
from mode_manager import ModeManager
from esp32_client import Esp32Client
from session_logger import SessionLogger


def test_mock_pipeline(tmp_path):
    cfg = BrainConfig(lab_mode=True, log_dir=tmp_path, session_log_path=tmp_path / "session.log")
    camera = CameraCapture(cfg)
    ocr = OCREngine(cfg)
    ai = AIEngine(cfg)
    modes = ModeManager()
    executor = Esp32Client(cfg)
    logger = SessionLogger(cfg.session_log_path)

    # Observe and OCR
    frame = camera.capture()
    text = ocr.extract_text(frame.data)
    assert "LAB MODE" in text or text

    # Suggest
    modes.set_mode("SUGGEST")
    proposal = ai.propose(text)
    logger.log(
        event_type="PROPOSAL",
        mode=modes.current,
        operator_id="op",
        details={"action_type": proposal["payload"]["type"], "payload_summary": proposal["payload"].get("text", "")[:32]},
        proposal_id=proposal["proposal_id"],
    )

    # Approve
    decision = {
        "proposal_id": proposal["proposal_id"],
        "decision": "APPROVED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operator_id": "op",
    }
    modes.set_mode("EXECUTE")
    executor.arm(True, physical_ok=True)
    execute_msg = {
        "execution_id": "exec_pipeline",
        "proposal_id": decision["proposal_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "EXECUTE",
        "action_type": "TYPE_TEXT",
        "payload": {"text": proposal["payload"].get("text", "")},
        "safety_bounds": {"max_text_length": 1024, "min_action_delay_ms": 100},
        "operator_approval": {"decision_timestamp": decision["timestamp"], "operator_id": decision["operator_id"]},
    }
    ack = executor.send_execute(execute_msg)
    assert ack["ok"] is True
    logger.log(
        event_type="EXECUTION",
        mode=modes.current,
        operator_id="op",
        details={"action_type": execute_msg["action_type"], "payload_summary": execute_msg["payload"].get("text", "")[:32]},
        proposal_id=proposal["proposal_id"],
        execution_id=execute_msg["execution_id"],
    )

    # Log file should have entries
    lines = cfg.session_log_path.read_text().strip().splitlines()
    assert len(lines) >= 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert second.get("previous_log_checksum") == first.get("checksum")
