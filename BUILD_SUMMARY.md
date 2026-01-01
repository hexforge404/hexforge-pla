# Build Summary — HexForge PLA (Portable Lab Assistant)

**Project Status**: Documentation Complete, Implementation Pending  
**Last Updated**: 2025-01-01  
**Target Completion**: Q2 2025 (3-4 months from start)

---

## Executive Summary

The HexForge Portable Lab Assistant (PLA) is an **internal lab tool** that combines:
- 📷 **Eyes**: USB webcam + OCR for screen reading
- 🧠 **Brain**: AI assistant (local LLM) for decision-making
- 🖱️ **Hands**: Bounded HID keyboard/mouse executor

**Key Safety Features**:
- Physical kill switch (hardware VBUS interrupt)
- Confirm-to-execute workflow (operator approves all actions)
- Command bounds (max 1024 chars, rate limit 100ms)
- Session logging (audit trail of all actions)
- "Smart brain, dumb hands" architecture (no autonomous control)

**Target Use Cases**:
- Automated UI testing in sandbox VMs
- Repetitive configuration tasks (form filling, wizard navigation)
- Lab environment troubleshooting assistance
- Research tool for UI automation techniques

---

## Repository Status

### ✅ Completed Documentation

| Document | Status | Purpose |
|----------|--------|---------|
| [README.md](README.md) | ✅ Complete | Project overview, safety warnings, quick start |
| [docs/00_PROJECT_CHARTER.md](docs/00_PROJECT_CHARTER.md) | ✅ Complete | Original project charter |
| [docs/00_PROJECT_OVERVIEW.md](docs/00_PROJECT_OVERVIEW.md) | ✅ Complete | High-level system overview |
| [docs/01_REPO_STRUCTURE.md](docs/01_REPO_STRUCTURE.md) | ✅ Complete | Repository organization |
| [docs/01_ARCHITECTURE.md](docs/01_ARCHITECTURE.md) | ✅ Complete | System architecture with 6 Mermaid/ASCII diagrams |
| [docs/02_SAFETY_GUARDRAILS.md](docs/02_SAFETY_GUARDRAILS.md) | ✅ Complete | Safety mechanisms and authorized use policy |
| [docs/03_ACTION_PROTOCOL.md](docs/03_ACTION_PROTOCOL.md) | ✅ Complete | Communication protocol specifications |
| [docs/04_HARDWARE_BOM.md](docs/04_HARDWARE_BOM.md) | ✅ Complete | Bill of materials with costs ($190-500) |
| [docs/05_SETUP_BRAIN_VM.md](docs/05_SETUP_BRAIN_VM.md) | ✅ Complete | Proxmox VM setup, Ubuntu install, Python environment |
| [docs/06_SETUP_CAMERA.md](docs/06_SETUP_CAMERA.md) | ✅ Complete | Camera positioning, v4l2 config, OCR calibration |
| [docs/07_SETUP_HID_EXECUTOR.md](docs/07_SETUP_HID_EXECUTOR.md) | ✅ Complete | Pico W firmware, kill switch wiring, safety testing |
| [docs/08_TEST_PLANS.md](docs/08_TEST_PLANS.md) | ✅ Complete | 5-phase testing with 40+ test cases |
| [docs/09_RUNBOOKS.md](docs/09_RUNBOOKS.md) | ✅ Complete | Operations, troubleshooting, emergency procedures |
| [docs/10_THREAT_MODEL.md](docs/10_THREAT_MODEL.md) | ✅ Complete | 9 threat scenarios with mitigations |

### ✅ Completed Code Scaffolds

| Component | Status | Purpose |
|-----------|--------|---------|
| [software/brain/README.md](software/brain/README.md) | ✅ Complete | Brain system overview and setup |
| [software/brain/requirements.txt](software/brain/requirements.txt) | ✅ Complete | Python dependencies (OpenCV, Tesseract, Flask, etc.) |
| [software/brain/config/brain_config.example.yaml](software/brain/config/brain_config.example.yaml) | ✅ Complete | Configuration template |
| [software/brain/src/main.py](software/brain/src/main.py) | ✅ Scaffold | Entry point with TODOs for implementation |
| [software/brain/tests/test_camera.py](software/brain/tests/test_camera.py) | ✅ Complete | Camera + OCR validation script |
| [software/brain/tests/test_hid_executor.py](software/brain/tests/test_hid_executor.py) | ✅ Complete | HID executor integration test |
| [hardware/pico-hid-executor/README.md](hardware/pico-hid-executor/README.md) | ✅ Complete | HID executor firmware overview |
| [hardware/pico-hid-executor/main.py](hardware/pico-hid-executor/main.py) | ✅ Complete | Full CircuitPython firmware with safety bounds |

### 🚧 Pending Implementation

| Component | Status | Priority | Effort |
|-----------|--------|----------|--------|
| Brain: camera.py | ❌ Not started | HIGH | 2-3 days |
| Brain: ai_engine.py | ❌ Not started | HIGH | 3-5 days |
| Brain: hid_interface.py | ❌ Not started | HIGH | 2 days |
| Brain: mode_manager.py | ❌ Not started | MEDIUM | 1-2 days |
| Brain: credential_detector.py | ❌ Not started | HIGH | 2-3 days |
| Brain: session_logger.py | ❌ Not started | MEDIUM | 1-2 days |
| Brain: web_ui/app.py | ❌ Not started | MEDIUM | 3-4 days |
| Brain: web_ui/templates/index.html | ❌ Not started | MEDIUM | 2-3 days |

---

## Implementation Roadmap

### Phase 1: Hardware Assembly (2 weeks)

**Goal**: Build and test physical components

- [ ] Procure parts from BOM (RPi4/Proxmox VM, Pico W, webcam, kill switch, LED)
- [ ] Assemble kill switch wiring (VBUS interrupt)
- [ ] Assemble HID ARMED LED (GPIO 2, 220Ω resistor)
- [ ] Flash CircuitPython on Pico W
- [ ] Install HID executor firmware (`main.py`)
- [ ] Test kill switch functionality (Phase 2 safety tests)
- [ ] Test LED indicator (Phase 2 safety tests)
- [ ] Mount webcam in lab (position 12-18" from target screen)

**Success Criteria**:
- Kill switch powers off Pico W instantly when toggled
- LED turns ON when mode=EXECUTE, OFF otherwise
- Pico W detected at `/dev/ttyACM0` on Brain VM
- Webcam detected at `/dev/video0` on Brain VM

---

### Phase 2: Brain System Setup (2 weeks)

**Goal**: Configure Brain VM and install dependencies

- [ ] Create Proxmox VM or set up RPi4
- [ ] Install Ubuntu Server 22.04 LTS
- [ ] Configure USB passthrough (webcam, HID executor)
- [ ] Install Python 3.11+, OpenCV, Tesseract OCR
- [ ] Install Ollama and pull `llama2:7b-chat` model
- [ ] Clone repository to `~/hexforge-pla`
- [ ] Create Python virtual environment
- [ ] Install Python dependencies from `requirements.txt`
- [ ] Configure `brain_config.yaml` (camera device, serial port, AI model)
- [ ] Run `test_camera.py` (validate camera + OCR)
- [ ] Run `test_hid_executor.py` (validate serial communication)

**Success Criteria**:
- Camera captures 1080p frames with <100ms latency
- OCR extracts text from camera feed with >90% accuracy
- Ollama responds to test prompts in <5 seconds
- Serial communication with HID executor working (115200 baud)

---

### Phase 3: Core Implementation (4-6 weeks)

**Goal**: Implement Brain software components

#### Week 1-2: Vision System
- [ ] Implement `camera.py` (OpenCV frame capture, OCR)
- [ ] Implement preprocessing (brightness/contrast adjustment)
- [ ] Test OCR accuracy on various screen types (terminal, web, code editor)
- [ ] Implement frame differencing (detect screen changes)

#### Week 3-4: AI Engine
- [ ] Implement `ai_engine.py` (Ollama API integration)
- [ ] Design system prompt (analyze screen, suggest actions, detect credentials)
- [ ] Implement credential detection patterns (AWS keys, SSH keys, password fields)
- [ ] Test AI suggestions on sample screens
- [ ] Implement suspicious command detection (rm -rf, sudo, exec, eval)

#### Week 5-6: HID Integration & Mode Manager
- [ ] Implement `hid_interface.py` (PySerial communication with Pico W)
- [ ] Implement JSON command serialization (type_text, key_combo, mouse_move)
- [ ] Implement `mode_manager.py` (OBSERVE/SUGGEST/EXECUTE state machine)
- [ ] Implement mode transition validation and logging
- [ ] Implement `session_logger.py` (audit logging with encryption)

**Success Criteria**:
- Brain captures screen, AI suggests action, logs observation (OBSERVE mode)
- Operator approves suggestion, HID executes, logs action (SUGGEST mode)
- Batch approval, HID executes workflow, logs all actions (EXECUTE mode)
- Credential detection working (flags AWS keys, SSH keys, passwords)

---

### Phase 4: Web UI & Testing (2-3 weeks)

**Goal**: Build operator interface and validate system

#### Week 1-2: Web UI
- [ ] Implement Flask app (`web_ui/app.py`)
- [ ] Implement authentication (username/password, Flask-Login)
- [ ] Implement dashboard (camera feed, AI suggestions, mode selector)
- [ ] Implement approval workflow (approve/reject buttons)
- [ ] Implement session log viewer
- [ ] Test web UI on desktop and tablet browsers

#### Week 3: Integration Testing
- [ ] Run Phase 1: Component Tests (camera, AI, HID)
- [ ] Run Phase 2: Safety Mechanism Tests (kill switch, bounds, credential detection)
- [ ] Run Phase 3: Integration Tests (end-to-end workflows)
- [ ] Run Phase 4: Stress Tests (100 actions, long sessions, complex screens)
- [ ] Run Phase 5: Security Tests (prompt injection, malicious JSON, log tampering)

**Success Criteria**:
- All Phase 1-2 tests pass (100% pass rate)
- Integration tests pass with <5% failure rate
- Stress tests pass with <10% failure rate
- Security tests pass (100% for critical scenarios)

---

### Phase 5: Deployment & Documentation (1 week)

**Goal**: Deploy to lab and train operators

- [ ] Install system in lab environment
- [ ] Configure lab network isolation
- [ ] Set up systemd service for Brain (`hexforge-pla-brain.service`)
- [ ] Create operator training materials
- [ ] Conduct operator training session
- [ ] Run final acceptance tests with operators
- [ ] Document lessons learned and edge cases

**Success Criteria**:
- System runs reliably in lab for 8 hours without crashes
- Operators can execute common workflows (login, form filling, config wizard)
- Operators understand kill switch and emergency procedures
- All session logs complete and tamper-evident

---

## Cost Summary

| Component | Cost Range | Notes |
|-----------|------------|-------|
| RPi4 Brain (4GB) | $100-120 | Or $0 if using Proxmox VM |
| Pico W + Kill Switch + LED | $36 | HID executor hardware |
| USB Webcam (1080p) | $55-95 | Logitech C920 recommended |
| Optional: E-ink display | $60-70 | Pi Zero 2 W + Waveshare display |
| Cables, enclosures, misc | $10-20 | USB extensions, breadboard, etc. |
| **Total (minimum viable)** | **$190-250** | RPi4 + Pico W + webcam |
| **Total (with Proxmox VM)** | **$90-130** | No RPi4 needed |
| **Total (complete)** | **$400-500** | All options + e-ink display |

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OCR accuracy insufficient | MEDIUM | HIGH | Use 1080p camera, optimize lighting, preprocess frames |
| AI model hallucination | MEDIUM | MEDIUM | Operator approval required, suspicious command detection |
| Serial communication flaky | LOW | MEDIUM | Add retries, timeout handling, connection monitoring |
| Kill switch mechanical failure | LOW | CRITICAL | Daily testing, backup: manual USB disconnect |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Operator approves malicious action | MEDIUM | HIGH | Training, credential detection warnings, 5-sec delay |
| Unauthorized use of system | LOW | HIGH | Physical security (locked lab), SSH key auth, session logging |
| Credential leakage via logs | MEDIUM | HIGH | Log encryption, auto-redaction, operator training |

### Security Risks

See [docs/10_THREAT_MODEL.md](docs/10_THREAT_MODEL.md) for detailed threat analysis.

---

## Success Criteria

### Minimum Viable Product (MVP)

- [x] Documentation complete (14 docs, 40+ pages)
- [ ] Hardware assembled and tested (kill switch, LED, camera, HID)
- [ ] Brain VM running with camera, OCR, AI model
- [ ] HID executor firmware functional (bounds enforced, LED working)
- [ ] OBSERVE mode working (camera → OCR → AI suggestions)
- [ ] SUGGEST mode working (operator approves actions)
- [ ] Phase 1-2 tests passed (component + safety tests)

### Full Production Release

- [ ] All MVP criteria met
- [ ] EXECUTE mode working (batch approval, workflow execution)
- [ ] Web UI functional (dashboard, approval workflow, session logs)
- [ ] Credential detection working (AWS keys, SSH keys, passwords)
- [ ] All 5 test phases passed (Phase 1-5, 40+ test cases)
- [ ] Operators trained and certified
- [ ] 30-day production trial completed without incidents

---

## Next Steps

1. **Procure Hardware** (Week 1)
   - Order parts from BOM
   - Set up Proxmox VM or RPi4

2. **Assemble Hardware** (Week 2)
   - Wire kill switch and LED
   - Flash HID executor firmware
   - Test kill switch and LED functionality

3. **Set Up Brain VM** (Week 3)
   - Install Ubuntu, dependencies
   - Configure camera and OCR
   - Test camera and HID executor integration

4. **Begin Core Implementation** (Week 4+)
   - Implement `camera.py`
   - Implement `ai_engine.py`
   - Implement `hid_interface.py`

---

## Lessons Learned (To Be Updated)

- TBD after Phase 1-2 completion
- TBD after integration testing
- TBD after production deployment

---

**See also**:
- [README.md](README.md) — Project overview
- [docs/01_ARCHITECTURE.md](docs/01_ARCHITECTURE.md) — System architecture
- [docs/04_HARDWARE_BOM.md](docs/04_HARDWARE_BOM.md) — Parts list
- [docs/08_TEST_PLANS.md](docs/08_TEST_PLANS.md) — Testing strategy
- [docs/09_RUNBOOKS.md](docs/09_RUNBOOKS.md) — Operations guide
