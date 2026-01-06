"""Deterministic AI proposal generator (stub).

This keeps behavior predictable and schema-valid for offline testing.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from config import BrainConfig
from contract_validator import validate_proposal


class AIEngine:
    def __init__(self, cfg: BrainConfig):
        self.cfg = cfg

    def propose(self, screen_text: str) -> Dict[str, Any]:
        truncated = (screen_text or "").strip()[: self.cfg.proposal_max_len]

        payload: Dict[str, Any]
        rationale = "Deterministic stub proposal based on OCR text."
        if "combo" in truncated.lower():
            payload = {"type": "KEY_COMBO", "keys": ["ctrl", "alt", "t"]}
            rationale = "Key combo suggested from OCR cue."
        elif "mouse" in truncated.lower():
            payload = {"type": "MOUSE_MOVE", "x": 10, "y": 10}
            rationale = "Mouse nudge suggested from OCR cue."
        elif "click" in truncated.lower():
            payload = {"type": "MOUSE_CLICK", "button": "left"}
            rationale = "Mouse click suggested from OCR cue."
        else:
            payload = {"type": "TYPE_TEXT", "text": truncated or "hello from pla"}

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "event_type": "action_proposal",
            "mode": "SUGGEST",
            "action_type": payload["type"],
            "payload": payload,
            "rationale": rationale,
            "credential_warning": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "created_at": int(time.time()),
            "safety_bounds": {"max_text_length": 1024, "min_action_delay_ms": 100},
        }
        ok, err = validate_proposal(proposal)
        if not ok:
            raise ValueError(f"proposal invalid: {err}")
        return proposal
