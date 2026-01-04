# PLA Node (Edge Tool-Runner)

Purpose: a minimal, authenticated system-introspection node that runs on the Raspberry Pi. The main Lab Assistant/orchestrator lives elsewhere and calls this node; this module is intentionally small and read-only (no arbitrary shell execution). The service is implemented in FastAPI (`app.fastapi_app:app`) and served by `uvicorn`.

## Endpoints (all JSON)
- `GET /health` (no auth) — readiness probe
- `POST /ingest` (auth if PLA_API_KEY set) — validate `contracts/event.schema.json`, enforce `event_version`, forward to Brain Receiver (127.0.0.1:8788/event), spool on failure, returns 202 Accepted
- `GET /status` (auth if PLA_API_KEY set) — gateway metrics: uptime, last ingest/forward times, success/failure counts, spool depth, retry_active

## Security Model
- Required header: `X-API-Key: <PLA_API_KEY>`
- Service refuses to start if `PLA_API_KEY` is unset (fail closed).
- No shell or exec endpoints; only curated read-only data.
- Recommend binding to LAN-only (0.0.0.0 on trusted subnet) and firewalling externally.

## Install (Raspberry Pi OS / Debian)
```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip git
cd ~/hexforge-pla/pla_node
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# generate a strong key
python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
# export your key
export PLA_API_KEY=<printed_key>
# run manually (foreground)
uvicorn app.fastapi_app:app --host 0.0.0.0 --port 8787
```

## systemd Deployment
1) Copy and edit env file (key only):
```bash
sudo mkdir -p /etc/pla_node
sudo cp config/pla.env.example /etc/pla_node/pla.env
sudo nano /etc/pla_node/pla.env  # set PLA_API_KEY
```
2) Copy service unit:
```bash
sudo cp deploy/pla-node.service /etc/systemd/system/pla-node.service
sudo systemctl daemon-reload
sudo systemctl enable pla-node
sudo systemctl start pla-node
sudo systemctl status pla-node
```
Service runs from `/home/pla/hexforge-pla/pla_node` by default; adjust `WorkingDirectory` if you install elsewhere.

Verify at runtime:
```bash
systemctl status pla-node --no-pager
ss -ltnp | grep ':8787'
curl http://127.0.0.1:8787/health
curl -H "X-API-Key: $PLA_API_KEY" -H "Content-Type: application/json" \
	-d @contracts/examples/button_press.json \
	http://127.0.0.1:8787/ingest
curl http://127.0.0.1:8787/openapi.json
curl -H "X-API-Key: $PLA_API_KEY" http://127.0.0.1:8787/status
```

## Curl Examples
```bash
curl http://<PI_IP>:8787/health
curl -H "X-API-Key: $PLA_API_KEY" -H "Content-Type: application/json" \
	-d @contracts/examples/button_press.json \
	http://<PI_IP>:8787/ingest
curl -H "X-API-Key: $PLA_API_KEY" http://<PI_IP>:8787/status
```

## Failure Simulation
- Stop Brain Receiver: `sudo systemctl stop brain-receiver`
- Ingest an event: `curl -H "X-API-Key: $PLA_API_KEY" -H "Content-Type: application/json" -d @contracts/examples/heartbeat.json http://127.0.0.1:8787/ingest`
- Check spool depth: `ls pla_node/spool` and `curl -H "X-API-Key: $PLA_API_KEY" http://127.0.0.1:8787/status`
- Restart Brain Receiver: `sudo systemctl start brain-receiver` and verify spool drains automatically (spool directory empties, status forward counts increase)

## Client Example (orchestrator-side)
A minimal stub lives in `client_example/call_node.py` showing how to call `/os-info` and `/usb-list` with `requests`.

## Smoke Test
Run `scripts/smoke_test.sh` while the server is up. It checks `/health` (unauth) and `/os-info` (auth) and fails fast on errors.

## Notes
- API key is optional; if set, requests must include `X-API-Key`.
- Logs are NDJSON; ingest/forward/retry outcomes are recorded with event_id and event_type.
- Events are validated against `contracts/event.schema.json`; if the Brain Receiver (port 8788) is down, events are spooled to `pla_node/spool/` and retried in the background.
