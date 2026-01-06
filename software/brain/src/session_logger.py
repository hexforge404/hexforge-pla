"""Session logger with checksum chaining that matches contract schema."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import uuid4

from contract_validator import validate_session_log


class SessionLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last_checksum = "0" * 64
        if path.exists():
            try:
                *_, last = path.read_text().strip().splitlines()
                self._last_checksum = json.loads(last).get("checksum", self._last_checksum)
            except Exception:
                pass

    def _canonical(self, obj: Dict[str, Any]) -> str:
        return json.dumps(obj, separators=(",", ":"), sort_keys=True)

    def log(
        self,
        *,
        event_type: str,
        mode: str,
        operator_id: str,
        details: Dict[str, Any],
        proposal_id: Optional[str] = None,
        execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).isoformat()
        log_id = uuid4().hex[:16]
        entry: Dict[str, Any] = {
            "log_id": log_id,
            "timestamp": ts,
            "event_type": event_type,
            "mode": mode,
            "operator_id": operator_id,
            "details": details,
            "checksum": "",
        }
        if proposal_id:
            entry["proposal_id"] = proposal_id
        if execution_id:
            entry["execution_id"] = execution_id
        if self._last_checksum:
            entry["previous_log_checksum"] = self._last_checksum

        canonical_entry = self._canonical({k: v for k, v in entry.items() if k != "checksum"})
        entry["checksum"] = hashlib.sha256((self._last_checksum + canonical_entry).encode("utf-8")).hexdigest()

        ok, err = validate_session_log(entry)
        if not ok:
            raise ValueError(f"session log invalid: {err}")

        with self.path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(entry) + "\n")
        self._last_checksum = entry["checksum"]
        return entry
