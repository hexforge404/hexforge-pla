# MVP Bring-up (Option A)

Minimal steps to exercise the Option A MVP path: Pi 4B Brain Receiver on port 8788 (default, env `BRAIN_RECEIVER_PORT`) + ESP32 "hands" sending button events every 5 seconds. The PLA Node service (if running) occupies 8787.

## What You Get
- HTTP POST /event endpoint on the Pi 4B
- JSON schema validation for button events
- Events logged to `logs/events.ndjson` with server timestamp
- ESP32 firmware that connects to Wi-Fi and sends a test button event repeatedly

## Prerequisites
- Raspberry Pi 4B with Python 3.11+, git, and outbound internet for pip
- ESP32 DevKit-style board (Wi-Fi capable) and USB cable
- Arduino IDE 2.x or Arduino CLI with ESP32 board support installed
- Pi and ESP32 on the same network; you know the Pi's IP address

## 1) Brain Receiver (Pi 4B)
1. SSH into the Pi and clone (or pull) this repo.
2. Start the receiver (creates `.venv`, installs deps, serves on 0.0.0.0:${BRAIN_RECEIVER_PORT:-8788} by default):
   ```bash
   cd ~/hexforge-pla/software/brain_receiver
   ./run.sh
   ```
3. Verify ports and health:
   ```bash
   ss -ltnp | grep -E ':(8787|8788)\b'
   curl http://127.0.0.1:8788/health
   ```
   Expected: `{ "ok": true, "status": "ready" }`
4. Send a sample event from any machine on the network:
   ```bash
   curl -X POST http://<PI4_IP>:8788/event \
     -H "Content-Type: application/json" \
     -d '{"device_id":"esp32-hands-001","type":"button_event","button":"MENU","state":"pressed","ts_ms":12345}'
   ```
   Expected: `{ "ok": true }`
5. Inspect the log (one JSON object per line):
   ```bash
   tail -n 5 ~/hexforge-pla/logs/events.ndjson
   ```

### Event Schema (Pi)
- `device_id`: string, required
- `type`: must equal `button_event`
- `button`: one of `MENU, OK, UP, DOWN, LEFT, RIGHT, BACK, POWER`
- `state`: `pressed` or `released`
- `ts_ms`: integer (client-side milliseconds)

## 2) ESP32 Firmware
1. Copy the config template and fill in your values:
   ```bash
   cd ~/hexforge-pla/hardware/esp32_hands_mvp
   cp config_template.h config.h
   # edit config.h -> WIFI_SSID, WIFI_PASSWORD, BRAIN_HOST (Pi IP), DEVICE_ID
   ```
2. Open `esp32_hands_mvp.ino` in Arduino IDE (or use Arduino CLI) and select:
   - Board: "ESP32 Dev Module" (or your exact ESP32 variant)
   - Port: the USB serial port for your board
3. Build and upload.
4. Open Serial Monitor at 115200 baud. You should see:
   - Wi-Fi connection message with assigned IP
   - A POST every ~5 seconds with status code and body
5. On the Pi, tail the log to confirm arrivals:
   ```bash
   tail -f ~/hexforge-pla/logs/events.ndjson
   ```

## Troubleshooting
- **HTTP 400 schema_validation_failed**: Check `button`/`state` values and that `type` is exactly `button_event`.
- **No log file created**: Ensure the receiver has write permission to `~/hexforge-pla/logs` and that it was started from `software/brain_receiver`.
- **Port already in use**: Stop conflicting services or set `BRAIN_RECEIVER_PORT` (default 8788; PLA Node uses 8787).
- **ESP32 stuck connecting to Wi-Fi**: Verify SSID/password, 2.4 GHz availability, and that MAC filtering is disabled.
- **No responses in Serial Monitor**: Re-check `BRAIN_HOST`, ensure Pi firewall allows 8787, and that the receiver is running.
- **Repeated reconnects**: Weak signal; move closer to the AP or use a better antenna.

## Next Steps
- Extend schema/button set in `software/brain_receiver/app.py` as the hardware grows.
- Swap the static test event for real button ISR hooks on the ESP32 when hardware is wired.
- Wrap the receiver in a systemd service on the Pi for auto-start.
