import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import BrainConfig
from web_ui.app import build_app


def _client():
    cfg = BrainConfig(lab_mode=True, operator_token="secret-token", require_physical_arm=True)
    app = build_app(cfg)
    return TestClient(app), cfg


def test_auth_required_for_mutations():
    client, _ = _client()
    r = client.post("/mode", json={"mode": "SUGGEST"})
    assert r.status_code == 401


def test_arm_and_execute_flow():
    client, cfg = _client()
    headers = {"X-Operator-Token": cfg.operator_token}

    # Move to SUGGEST and propose
    assert client.post("/mode", json={"mode": "SUGGEST"}, headers=headers).status_code == 200
    prop = client.post("/propose", json={"text": "hi"}, headers=headers)
    assert prop.status_code == 200

    # Decision without arm should fail
    denied = client.post("/decide", json={"approved": True}, headers=headers)
    assert denied.status_code == 403

    # Arm and switch to EXECUTE
    assert client.post("/arm", json={"enabled": True, "physical_ok": True}, headers=headers).status_code == 200
    assert client.post("/mode", json={"mode": "EXECUTE"}, headers=headers).status_code == 200

    # Now decision should execute
    decision = client.post("/decide", json={"approved": True}, headers=headers)
    assert decision.status_code == 200
    body = decision.json()
    assert body.get("ack", {}).get("ok") is True
