# PLA Node (Edge Tool-Runner)

Purpose: a minimal, authenticated system-introspection node that runs on the Raspberry Pi. The main Lab Assistant/orchestrator lives elsewhere and calls this node; this module is intentionally small and read-only (no arbitrary shell execution).

## Endpoints (all JSON)
- `GET /health` (no auth) — readiness probe
- `GET /os-info` (auth) — hostname, platform, kernel, arch
- `GET /disk` (auth) — root filesystem usage via psutil
- `GET /usb-list` (auth) — `lsusb` + `lsblk` output (read-only)
- `GET /ip` (auth) — local IPv4 addresses per interface
- `GET /docker/ps` (auth, optional) — docker ps output if Docker exists, else 501

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
uvicorn app.main:app --host 0.0.0.0 --port 8787
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
Service runs from `/opt/pla_node` by default; adjust `WorkingDirectory` if you install elsewhere.

## Curl Examples
```bash
curl http://<PI_IP>:8787/health
curl -H "X-API-Key: $PLA_API_KEY" http://<PI_IP>:8787/os-info
curl -H "X-API-Key: $PLA_API_KEY" http://<PI_IP>:8787/usb-list
```

## Client Example (orchestrator-side)
A minimal stub lives in `client_example/call_node.py` showing how to call `/os-info` and `/usb-list` with `requests`.

## Smoke Test
Run `scripts/smoke_test.sh` while the server is up. It checks `/health` (unauth) and `/os-info` (auth) and fails fast on errors.

## Notes
- Keep the API key secret; never log it. Logs capture timestamp, path, caller IP, and success/failure only.
- Extend endpoints cautiously; do not add arbitrary command execution without new guardrails.
