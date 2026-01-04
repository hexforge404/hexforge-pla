import time
from datetime import datetime, timezone

import httpx
import pytest

from pla_node.app import fastapi_app


@pytest.fixture(autouse=True)
def reset_state(tmp_path):
    # Clear spool directory and reset metrics for isolation across tests.
    for path in fastapi_app.SPOOL_DIR.glob("*.ndjson"):
        path.unlink(missing_ok=True)
    fastapi_app.metrics.update(
        {
            "last_ingest_ts": None,
            "last_forward_success_ts": None,
            "last_forward_failure_ts": None,
            "forward_success_count": 0,
            "forward_failure_count": 0,
        }
    )


@pytest.fixture()
async def client():
    transport = httpx.ASGITransport(app=fastapi_app.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture()
def valid_payload():
    return {
        "event_version": "1.0",
        "device_id": "dev-1",
        "event_type": "button_press",
        "ts": datetime.now(timezone.utc).isoformat(),
        "seq": 1,
        "payload": {"pressed": True},
    }


@pytest.mark.anyio
async def test_ingest_rejects_invalid_json(client):
    resp = await client.post("/ingest", content=b"not-json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_json"


@pytest.mark.anyio
async def test_ingest_accepts_and_forwards(client, valid_payload, monkeypatch):
    forwards = []

    def fake_forward_event(payload, request_id, timeout=3.0):  # noqa: ARG001
        forwards.append(payload["seq"])

    monkeypatch.setattr(fastapi_app, "_forward_event", fake_forward_event)

    resp = await client.post("/ingest", json=valid_payload)
    assert resp.status_code == 202
    assert resp.json()["ok"] is True

    # Background task should forward once.
    for _ in range(10):
        if forwards:
            break
        time.sleep(0.05)
    assert forwards == [1]


@pytest.mark.anyio
async def test_ingest_spools_on_forward_failure(client, valid_payload, monkeypatch):
    spooled = []

    def fake_forward_event(payload, request_id, timeout=3.0):  # noqa: ARG001
        raise RuntimeError("fail")

    def fake_write_spool(payload):
        spooled.append(payload)

    monkeypatch.setattr(fastapi_app, "_forward_event", fake_forward_event)
    monkeypatch.setattr(fastapi_app, "_write_spool", fake_write_spool)

    resp = await client.post("/ingest", json=valid_payload)
    assert resp.status_code == 202

    for _ in range(10):
        if spooled:
            break
        time.sleep(0.05)

    assert len(spooled) == 1
    assert spooled[0]["seq"] == valid_payload["seq"]


@pytest.mark.anyio
async def test_ingest_schema_validation_failure(client, valid_payload):
    bad_payload = dict(valid_payload)
    bad_payload.pop("event_type")

    resp = await client.post("/ingest", json=bad_payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "schema_validation_failed"
    assert "event_type" in body["details"]
