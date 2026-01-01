# Brain Software — HexForge PLA

**Purpose**: AI-powered vision and decision-making system  
**Language**: Python 3.11+  
**Platform**: Ubuntu Server 22.04 (Proxmox VM or Raspberry Pi 4)

---

## Architecture

```
software/brain/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config/
│   └── brain_config.yaml     # System configuration
├── src/
│   ├── main.py               # Entry point
│   ├── camera.py             # Camera capture & OCR
│   ├── ai_engine.py          # LLM integration (Ollama)
│   ├── hid_interface.py      # Serial communication with Pico W
│   ├── mode_manager.py       # OBSERVE/SUGGEST/EXECUTE state machine
│   ├── credential_detector.py # Credential pattern matching
│   └── session_logger.py     # Audit logging
├── tests/
│   ├── test_camera.py        # Camera + OCR validation
│   ├── test_ocr.py           # OCR accuracy tests
│   └── test_hid_executor.py  # HID integration test
└── web_ui/
    ├── app.py                # Flask web interface
    └── templates/
        └── index.html        # Operator dashboard
```

---

## Setup

### Install Dependencies

```bash
cd ~/hexforge-pla/software/brain
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure System

```bash
cp config/brain_config.example.yaml config/brain_config.yaml
nano config/brain_config.yaml
# Edit camera device, AI model, HID executor serial port
```

### Test Components

```bash
# Test camera
python tests/test_camera.py

# Test OCR
python tests/test_ocr.py

# Test HID executor (requires Pico W connected)
python tests/test_hid_executor.py
```

---

## Running the System

### Start Brain Service

```bash
cd ~/hexforge-pla/software/brain
source venv/bin/activate
python src/main.py
```

### Access Web UI

Open browser: `http://<VM_IP>:5000`

Default credentials:
- Username: `operator`
- Password: `hexforge2025` (change after first login)

---

## Configuration Reference

See `config/brain_config.yaml` for all options:

- **system.mode**: Default operating mode (`observe`, `suggest`, `execute`)
- **camera.device**: Video device path (e.g., `/dev/video0`)
- **camera.resolution**: Capture resolution `[width, height]`
- **vision.ocr_engine**: OCR backend (`tesseract`)
- **ai.backend**: AI backend (`ollama`)
- **ai.model**: LLM model name (`llama2:7b-chat`)
- **hid_executor.device**: Serial port for Pico W (e.g., `/dev/ttyACM0`)
- **safety.max_action_length**: Maximum characters per HID command (1024)
- **safety.rate_limit_ms**: Minimum delay between HID actions (100ms)
- **safety.require_approval**: Force operator approval for EXECUTE mode actions (true)

---

## API Endpoints

### Mode Management

```bash
# Get current mode
curl http://localhost:5000/api/mode

# Set mode to SUGGEST
curl -X POST http://localhost:5000/api/mode -d '{"mode":"SUGGEST"}'
```

### Action Approval

```bash
# Get pending suggestions
curl http://localhost:5000/api/suggestions

# Approve suggestion
curl -X POST http://localhost:5000/api/approve -d '{"suggestion_id":123}'

# Reject suggestion
curl -X POST http://localhost:5000/api/reject -d '{"suggestion_id":123}'
```

### System Status

```bash
# Health check
curl http://localhost:5000/api/health

# Camera feed (MJPEG stream)
curl http://localhost:5000/api/camera/stream
```

---

## Development

### Code Style

- PEP 8 compliant
- Type hints required for public functions
- Docstrings for all modules, classes, functions

### Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Logging

Logs written to:
- `/var/log/hexforge-pla/brain.log` (application logs)
- `/var/log/hexforge-pla/sessions/` (session audit logs)

---

## Safety Notes

- **Always start in OBSERVE mode** (default)
- **Operator must approve each action** in SUGGEST/EXECUTE modes
- **Keep kill switch accessible** when HID executor is armed
- **Review session logs** after each session for anomalies

---

**See also**:
- [Architecture](../../docs/01_ARCHITECTURE.md)
- [Setup Brain VM](../../docs/05_SETUP_BRAIN_VM.md)
- [Test Plans](../../docs/08_TEST_PLANS.md)
