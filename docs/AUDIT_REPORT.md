# PLA Brain Audit Report (2026-01-05)

## Current Health
- Brain FastAPI app boots in lab mode, enforces operator token on all mutations, and exposes status/ocr/propose/decide/arm endpoints in [software/brain/src/web_ui/app.py](software/brain/src/web_ui/app.py#L23-L214).
- Proposal generation is deterministic and contract-valid with top-level `action_type`, ISO timestamp, and safety bounds in [software/brain/src/ai_engine.py](software/brain/src/ai_engine.py#L1-L52).
- ESP32 client stubs heartbeat and acknowledges in lab mode while enforcing arm + physical_ok + contract bounds and rate-limit in [software/brain/src/esp32_client.py](software/brain/src/esp32_client.py#L18-L121).
- Configuration is centralized with env overrides for lab_mode, operator_token, serial bounds, and physical arm requirement in [software/brain/src/config.py](software/brain/src/config.py#L1-L95).

## Test Status
- Command: `. .venv/bin/activate && LAB_MODE=true pytest -q software/brain/tests`
- Result: **22 passed, 7 skipped** (hardware HID suite plus camera/OCR tests skipped when no device/frame).
- Skipped: hardware-dependent HID executor integration in [software/brain/tests/test_hid_executor.py](software/brain/tests/test_hid_executor.py) and camera/OCR tests when `/dev/video0` unavailable.

## Safety & Auth Controls
- Mutations require `X-Operator-Token`; unauthorized requests return 401 in [software/brain/src/web_ui/app.py](software/brain/src/web_ui/app.py#L41-L44).
- Execute path is gated by mode EXECUTE, logical arm, and physical arm flag (configurable) before sending to executor in [software/brain/src/web_ui/app.py](software/brain/src/web_ui/app.py#L177-L211).
- Executor rejects commands without arm or physical_ok and checks heartbeat (production) and contract bounds (text length, allowed keys) in [software/brain/src/esp32_client.py](software/brain/src/esp32_client.py#L54-L85).
- Proposal and execute messages include safety bounds (`max_text_length` 1024, `min_action_delay_ms` 100) in [software/brain/src/ai_engine.py](software/brain/src/ai_engine.py#L38-L49) and [software/brain/src/web_ui/app.py](software/brain/src/web_ui/app.py#L185-L199).

## Known Gaps / Risks
- Hardware coverage: HID executor suite is skipped; real-device regressions will not be caught until re-enabled with hardware attached.
- Camera/OCR tests are skipped if no `/dev/video0`; no automated coverage without attached camera.
- Heartbeat in lab mode is simulated; production heartbeat freshness check only applies when `lab_mode` is false, so ensure real executor emits device_status at least every `status_heartbeat_s` seconds.
- Env defaults set `PLA_EXEC_MIN_DELAY` to 0.2s while in-code default is 0.1s; confirm intended minimum action spacing.

## Recommended Next Actions
- Re-enable and adapt [software/brain/tests/test_hid_executor.py](software/brain/tests/test_hid_executor.py) for your hardware lab to regain end-to-end coverage.
- Provide a camera stub or attach `/dev/video0` if you want camera/OCR tests to run in CI.
- Document operator token and physical arm switch configuration in deployment docs; consider adding a health endpoint that surfaces heartbeat freshness and arm state.
- If running outside lab mode, validate serial heartbeat cadence against `status_heartbeat_s` and ensure executor firmware emits device_status regularly.

## How to Run
- App: `. .venv/bin/activate && LAB_MODE=true uvicorn web_ui.app:build_app` (pass real config via env vars from [software/brain/src/config.py](software/brain/src/config.py#L60-L90)).
- Tests: `. .venv/bin/activate && LAB_MODE=true pytest -q software/brain/tests`.
- Firmware: build/upload via PlatformIO under `esp32_firmware/` (composite HID with ArduinoJson, heartbeat and arm GPIO).
