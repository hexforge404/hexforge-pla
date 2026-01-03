# Repository Structure — HexForge PLA

**Purpose**: Clean, modular organization that separates hardware, software, contracts, and documentation.

---

## Current Structure

```
hexforge-pla/
├── contracts/              # Contract system (JSON schemas, validation specs)
│   ├── schemas/            # 7 JSON schemas (5 PLA + 2 global)
│   ├── CONTRACTS_INDEX.md
│   ├── GLOBAL_CONTRACT_MAPPING.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── CHANGELOG.md
│   └── GLOBAL_INTEGRATION_STATUS.md
│
├── docs/                   # All documentation
│   ├── 00_PROJECT_CHARTER.md
│   ├── 00_PROJECT_OVERVIEW.md
│   ├── 01_ARCHITECTURE.md
│   ├── 01_REPO_STRUCTURE.md
│   ├── 02_SAFETY_GUARDRAILS.md
│   ├── 03_ACTION_PROTOCOL.md
│   ├── 04_HARDWARE_BOM.md
│   ├── 05_SETUP_BRAIN_VM.md
│   ├── 06_SETUP_CAMERA.md
│   ├── 07_SETUP_HID_EXECUTOR.md
│   ├── 08_TEST_PLANS.md
│   ├── 09_RUNBOOKS.md
│   ├── 10_THREAT_MODEL.md
│   └── CHATGPT_CONTEXT_PACK.md
│
├── hardware/               # Hardware-specific code
│   ├── pico-hid-executor/  # Raspberry Pi Pico W HID firmware
│   │   ├── main.py         # Firmware entry point (337 lines)
│   │   ├── contract_validator.py  # Lightweight validation (130 lines)
│   │   └── README.md
│   │
│   └── eink-status-totem/  # E-ink status display (optional)
│       └── (future)
│
├── software/               # Software services
│   ├── brain/              # Main AI/control system
│   │   ├── src/
│   │   │   ├── main.py     # Entry point (115 lines, scaffolding)
│   │   │   └── contract_validator.py  # Full validation (225 lines)
│   │   ├── tests/
│   │   │   ├── fixtures/   # 13 JSON test fixtures
│   │   │   ├── test_contracts.py  # 15/15 passing
│   │   │   ├── test_camera.py
│   │   │   └── test_hid_executor.py
│   │   ├── config/
│   │   └── requirements.txt
│   │
│   └── ui/                 # Web control interface (future)
│       └── (not started)
│
├── scripts/                # Automation and deployment
│   ├── deploy/
│   └── dev/
│
├── logs/                   # Runtime logs (gitignored)
│
├── README.md               # Main entry point
└── .gitignore
```

---

## Proposed Enhancements

### Additional Directories (Future)

```
hexforge-pla/
├── hardware/
│   ├── pico-hid-executor/      # ✅ Exists
│   ├── eink-status-totem/      # ✅ Exists (placeholder)
│   ├── camera-mount/           # 📐 CAD files for webcam mount
│   └── integration-diagrams/   # 🔌 Wiring diagrams, pinouts
│
├── software/
│   ├── brain/
│   │   ├── src/
│   │   │   ├── camera/         # 📷 Camera capture module
│   │   │   ├── ai_engine/      # 🧠 AI reasoning engine
│   │   │   ├── hid_interface/  # 🖱️ HID communication
│   │   │   ├── mode_manager/   # 🔄 State machine
│   │   │   └── session_logger/ # 📝 Audit logging
│   │   └── ui/                 # 🌐 Web control panel
│
├── configs/                    # 🔧 Configuration templates
│   ├── brain_config.yaml.example
│   ├── camera_config.yaml.example
│   └── hid_config.yaml.example
│
└── tools/                      # 🛠️ Development utilities
    ├── schema_validator.py     # Manual schema testing
    ├── serial_monitor.py       # HID executor debugging
    └── log_analyzer.py         # Session log analysis
```

---

## Module Isolation Strategy

### 1. Hardware Services (Independent)

**pico-hid-executor** (Current: `hardware/pico-hid-executor/`)
- Language: CircuitPython
- Dependencies: Minimal (adafruit_hid)
- Interface: USB serial (JSON commands)
- Deployment: Flash to Pico W
- Testing: Integration tests only (requires hardware)
- Status: ✅ Functional

**eink-status-totem** (Proposed: `hardware/eink-status-totem/`)
- Language: CircuitPython or MicroPython
- Dependencies: Display driver (waveshare/adafruit)
- Interface: I2C or SPI from Brain
- Deployment: Flash to display controller
- Testing: Display rendering tests
- Status: 📋 Planned

---

### 2. Brain Services (Modular)

**Camera Service** (Proposed: `software/brain/src/camera/`)
- Purpose: Frame capture, OCR, preprocessing
- Interface: Python module (CameraCapture class)
- Dependencies: OpenCV, Tesseract
- Testing: Unit tests (mock frames) + integration (real camera)
- Status: ❌ Not started

**AI Engine Service** (Proposed: `software/brain/src/ai_engine/`)
- Purpose: Screen analysis, action proposals, reasoning
- Interface: Python module (AIEngine class)
- Dependencies: Ollama, transformers
- Testing: Unit tests (mock OCR) + integration (real AI)
- Status: ❌ Not started

**HID Interface Service** (Proposed: `software/brain/src/hid_interface/`)
- Purpose: Serial communication with HID executor
- Interface: Python module (HIDInterface class)
- Dependencies: pyserial
- Testing: Unit tests (mock serial) + integration (real HID)
- Status: ❌ Not started

**Mode Manager Service** (Proposed: `software/brain/src/mode_manager/`)
- Purpose: State machine (OBSERVE/SUGGEST/EXECUTE)
- Interface: Python module (ModeManager class)
- Dependencies: None (pure logic)
- Testing: Unit tests (state transitions)
- Status: ❌ Not started

**Session Logger Service** (Proposed: `software/brain/src/session_logger/`)
- Purpose: Immutable audit trail with checksums
- Interface: Python module (SessionLogger class)
- Dependencies: hashlib (stdlib)
- Testing: Unit tests (log integrity)
- Status: ❌ Not started

**Web UI Service** (Proposed: `software/brain/ui/`)
- Purpose: Control panel, proposal approval, log viewer
- Interface: Flask/FastAPI web server
- Dependencies: Flask/FastAPI, websockets
- Testing: Frontend tests (playwright) + API tests
- Status: ❌ Not started

---

### 3. Contract Validation (Shared Library)

**Contract Validator** (Current: `software/brain/src/contract_validator.py`)
- Purpose: JSON schema validation for all messages
- Interface: Python module (validate_* functions)
- Dependencies: jsonschema
- Testing: ✅ 15/15 tests passing
- Status: ✅ Complete

---

## Service Communication Patterns

### Brain ↔ HID Executor
```
Protocol: USB Serial (115200 baud)
Format: JSON (newline-delimited)
Contracts:
  - Brain → HID: action_execute.schema.json
  - HID → Brain: device_status.schema.json
```

### Brain ↔ Web UI
```
Protocol: WebSocket (real-time) + REST (control)
Format: JSON
Contracts:
  - Brain → UI: action_proposal.schema.json
  - UI → Brain: action_decision.schema.json
```

### Brain → Session Log
```
Protocol: File I/O (append-only)
Format: JSON Lines
Contracts:
  - All events: session_log.schema.json
```

### Brain ↔ E-ink Display (Optional)
```
Protocol: I2C or SPI
Format: Custom (display commands)
No contracts (hardware-specific)
```

---

## File Naming Conventions

### Python Modules
- Use snake_case: `camera_capture.py`, `ai_engine.py`
- Main entry points: `main.py`, `__main__.py`
- Tests: `test_<module>.py`

### Configuration Files
- Use lowercase with underscores: `brain_config.yaml`
- Examples: `*.example` suffix
- Secrets: `*.secret` (gitignored)

### Documentation
- Use numbered prefixes for reading order: `01_ARCHITECTURE.md`
- Use uppercase for titles: `CONTRACTS_INDEX.md`
- Use descriptive names: `CHATGPT_CONTEXT_PACK.md`

### Hardware Files
- Use descriptive names: `main.py`, `contract_validator.py`
- READMEs: `README.md` (uppercase)

---

## Dependency Management

### Brain (Python 3.11+)
```txt
# software/brain/requirements.txt
jsonschema==4.20.0          # Contract validation
opencv-python==4.8.1        # Camera capture
pytesseract==0.3.10         # OCR
pyserial==3.5               # HID communication
flask==3.0.0                # Web UI (if using Flask)
pyyaml==6.0.1               # Configuration
```

### HID Executor (CircuitPython 8.x)
```txt
# hardware/pico-hid-executor/requirements.txt
adafruit-circuitpython-hid  # HID keyboard/mouse
# Note: No external package manager, use bundle
```

---

## Development Workflow

### 1. Clone Repository
```bash
git clone <repo-url> hexforge-pla
cd hexforge-pla
```

### 2. Setup Brain Environment
```bash
cd software/brain
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Contract Tests
```bash
python3 tests/test_contracts.py
# Expected: 15/15 tests passed
```

### 4. Flash HID Executor
```bash
# Copy CircuitPython firmware to Pico W
# Copy hardware/pico-hid-executor/* to CIRCUITPY drive
```

### 5. Start Brain (Scaffolding)
```bash
cd software/brain
python3 src/main.py
# Currently: Placeholder only
```

---

## Gitignore Strategy

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
venv/
.venv/
*.egg-info/

# Logs
logs/*.log
*.log

# Configuration (secrets)
*.secret
*_secret.yaml

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Hardware (temporary)
*.uf2  # Compiled firmware (regenerate)

# Testing
.pytest_cache/
.coverage
htmlcov/
```

---

## Migration Path (Current → Proposed)

### Phase 1: Current State ✅
- Contracts complete
- HID executor functional
- Documentation comprehensive
- Brain scaffolding in place

### Phase 2: Modularization (Next)
1. Create `software/brain/src/camera/` module
2. Create `software/brain/src/ai_engine/` module
3. Create `software/brain/src/hid_interface/` module
4. Refactor `main.py` to use modules

### Phase 3: UI Implementation
1. Create `software/brain/ui/` service
2. Implement control panel
3. Implement proposal approval interface
4. Implement session log viewer

### Phase 4: Hardware Expansion (Optional)
1. Implement `hardware/eink-status-totem/`
2. Add CAD files for mounts
3. Add wiring diagrams

---

## Status Summary

| Component | Location | Status | Lines | Tests |
|-----------|----------|--------|-------|-------|
| Contracts | `contracts/` | ✅ Complete | ~1000 | 15/15 |
| HID Executor | `hardware/pico-hid-executor/` | ✅ Functional | 467 | Integration |
| Brain Scaffold | `software/brain/src/` | 🚧 Scaffold | 340 | 15/15 (contracts) |
| Camera Module | `software/brain/src/camera/` | ❌ Missing | 0 | 0 |
| AI Engine | `software/brain/src/ai_engine/` | ❌ Missing | 0 | 0 |
| Web UI | `software/brain/ui/` | ❌ Missing | 0 | 0 |
| Session Logger | `software/brain/src/session_logger/` | ❌ Missing | 0 | 0 |
| Documentation | `docs/` | ✅ Complete | ~3000 | N/A |

**Overall MVP Progress**: ~30%

---

**Last Updated**: 2026-01-01  
**Next Review**: After camera/AI module implementation
