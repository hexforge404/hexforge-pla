"""FastAPI application for PLA Brain operator UI and API."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status as http_status
from fastapi.responses import HTMLResponse

from config import BrainConfig, ensure_log_dirs
from camera import CameraCapture
from ocr import OCREngine
from ai_engine import AIEngine
from mode_manager import ModeManager
from esp32_client import Esp32Client
from session_logger import SessionLogger
from contract_validator import validate_decision


def build_app(cfg: BrainConfig) -> FastAPI:
    ensure_log_dirs(cfg)
    camera = CameraCapture(cfg)
    ocr = OCREngine(cfg)
    ai = AIEngine(cfg)
    modes = ModeManager()
    executor = Esp32Client(cfg)
    logger = SessionLogger(cfg.session_log_path)

    state: Dict[str, Any] = {
        "last_text": "",
        "last_proposal": None,
        "last_decision": None,
        "last_execute": None,
        "last_ack": None,
        "operator_id": "operator_lab",
    }

    def require_auth(x_operator_token: str = Header(default=None)) -> None:
        if x_operator_token != cfg.operator_token:
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="invalid operator token")

    app = FastAPI(title="HexForge PLA Brain", version="0.1.0", docs_url="/openapi")

    @app.get("/health")
    def health():
        return {"ok": True, "lab_mode": cfg.lab_mode, "mode": modes.current}

    @app.get("/")
    def index():
        return HTMLResponse(
            """
            <html><body style='font-family: monospace; background: #0b0f16; color: #e8f0ff;'>
            <h2>PLA Brain</h2>
            <p>Mode: <span id='mode'></span></p>
            <p>Lab mode: {lab}</p>
            <button onclick="setMode('OBSERVE')">OBSERVE</button>
            <button onclick="setMode('SUGGEST')">SUGGEST</button>
            <button onclick="setMode('EXECUTE')">EXECUTE</button>
            <pre id='status'></pre>
            <script>
            async function refresh() {{
              const res = await fetch('/status');
              const data = await res.json();
              document.getElementById('status').textContent = JSON.stringify(data, null, 2);
              document.getElementById('mode').textContent = data.mode;
            }}
            async function setMode(mode) {{
              await fetch('/mode', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{mode}})}});
              refresh();
            }}
            refresh(); setInterval(refresh, 2000);
            </script>
            </body></html>
            """.format(lab=str(cfg.lab_mode))
        )

    @app.get("/status")
    def get_status():
        return {
            "mode": modes.current,
            "armed": executor._armed,  # simple surface for now
            "physical_ok": executor._physical_ok,
            "lab_mode": cfg.lab_mode,
            "last_proposal": state["last_proposal"],
            "last_decision": state["last_decision"],
            "last_execute": state["last_execute"],
            "last_ack": state["last_ack"],
            "device_status": executor.read_status(),
        }

    @app.post("/mode")
    def set_mode(body: Dict[str, str], _: None = Depends(require_auth)):
        new_mode = body.get("mode", "").upper()
        old = modes.current
        modes.set_mode(new_mode)
        logger.log(
            event_type="MODE_CHANGE",
            mode=modes.current,
            operator_id=state["operator_id"],
            details={"old_mode": old, "new_mode": new_mode},
        )
        return {"ok": True, "mode": modes.current}

    @app.get("/frame.jpg")
    def frame():
        frm = camera.capture()
        return Response(content=frm.to_jpeg_bytes(), media_type="image/jpeg")

    @app.get("/ocr")
    def ocr_text():
        frm = camera.capture()
        text = ocr.extract_text(frm.data)
        state["last_text"] = text
        return {"text": text}

    @app.post("/propose")
    def propose(body: Dict[str, Any] | None = None, _: None = Depends(require_auth)):
        if not modes.can_propose:
            raise HTTPException(status_code=403, detail="mode does not allow proposals")
        text = (body or {}).get("text") or state["last_text"]
        proposal = ai.propose(text)
        state["last_proposal"] = proposal
        logger.log(
            event_type="PROPOSAL",
            mode=modes.current,
            operator_id=state["operator_id"],
            details={
                "action_type": proposal["payload"]["type"],
                "payload_summary": proposal["payload"].get("text", "")[:64],
                "credential_warning": proposal.get("credential_warning", False),
            },
            proposal_id=proposal["proposal_id"],
        )
        return proposal

    @app.post("/arm")
    def arm(body: Dict[str, Any], _: None = Depends(require_auth)):
        enable = bool(body.get("enabled", False))
        physical_ok = bool(body.get("physical_ok", False)) or not cfg.require_physical_arm
        executor.arm(enable, physical_ok=physical_ok)
        logger.log(
            event_type="MODE_CHANGE",
            mode=modes.current,
            operator_id=state["operator_id"],
            details={"armed": enable, "physical_ok": physical_ok},
        )
        return {"ok": True, "armed": executor._armed, "physical_ok": executor._physical_ok}

    @app.post("/decide")
    def decide(body: Dict[str, Any], _: None = Depends(require_auth)):
        if state.get("last_proposal") is None:
            raise HTTPException(status_code=400, detail="no proposal to decide")
        decision_flag = "APPROVED" if body.get("approved") else "REJECTED"
        decision = {
            "proposal_id": state["last_proposal"]["proposal_id"],
            "decision": decision_flag,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operator_id": body.get("operator_id") or state["operator_id"],
        }
        if decision_flag == "REJECTED":
            decision["override_reason"] = body.get("reason", "unsafe")
        ok, err = validate_decision(decision)
        if not ok:
            raise HTTPException(status_code=400, detail=f"decision invalid: {err}")
        state["last_decision"] = decision
        logger.log(
            event_type="DECISION",
            mode=modes.current,
            operator_id=decision["operator_id"],
            details={"decision": decision_flag, "proposal_id": decision["proposal_id"]},
            proposal_id=decision["proposal_id"],
        )

        if decision_flag == "APPROVED":
            if modes.current != "EXECUTE":
                raise HTTPException(status_code=403, detail="not in execute mode")
            if not executor._armed:
                raise HTTPException(status_code=403, detail="executor not armed")
            if cfg.require_physical_arm and not executor._physical_ok:
                raise HTTPException(status_code=403, detail="physical arm not confirmed")
            prop_payload = state["last_proposal"]["payload"]
            action_type = prop_payload.get("type", "TYPE_TEXT")
            payload = {k: v for k, v in prop_payload.items() if k != "type"}
            execute_msg = {
                "execution_id": uuid.uuid4().hex[:16],
                "proposal_id": decision["proposal_id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mode": "EXECUTE",
                "action_type": action_type,
                "payload": payload,
                "safety_bounds": {"max_text_length": 1024, "min_action_delay_ms": 100},
                "operator_approval": {
                    "decision_timestamp": decision["timestamp"],
                    "operator_id": decision["operator_id"],
                },
            }
            ack = executor.send_execute(execute_msg)
            state["last_execute"] = execute_msg
            state["last_ack"] = ack
            logger.log(
                event_type="EXECUTION",
                mode=modes.current,
                operator_id=decision["operator_id"],
                details={"action_type": execute_msg["action_type"], "payload_summary": execute_msg["payload"].get("text", "")[:64]},
                proposal_id=execute_msg["proposal_id"],
                execution_id=execute_msg["execution_id"],
            )
            return {"decision": decision, "ack": ack}
        return {"decision": decision}

    return app
