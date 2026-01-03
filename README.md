# HexForge Portable Lab Assistant (PLA)

**Internal-only lab tool**: Camera vision ("eyes") + bounded HID executor ("hands") + AI assistant ("brain") with confirm-to-execute guardrails.

> ⚠️ **SAFETY FIRST**: This tool executes keyboard/mouse actions. Physical kill switch required. Use only on authorized, operator-owned systems.

---

## Quick Start

1. **Understand the system**: Read [Project Charter](docs/00_PROJECT_CHARTER.md) and [Architecture](docs/01_ARCHITECTURE.md)
2. **Review safety**: Read [Safety Guardrails](docs/02_SAFETY_GUARDRAILS.md) and [Threat Model](docs/10_THREAT_MODEL.md)
3. **Gather hardware**: See [Hardware BOM](docs/04_HARDWARE_BOM.md)
4. **Build it**: Follow setup guides (Brain, Camera, HID Executor)
5. **Test thoroughly**: Run [Test Plans](docs/08_TEST_PLANS.md) - **all safety tests must pass**
6. **Operate safely**: Use [Runbooks](docs/09_RUNBOOKS.md) for daily operations

## MVP Bring-up (Option A)

- Start Brain Receiver: `cd software/brain_receiver && ./run.sh` (serves on 0.0.0.0:8787 and writes logs/events.ndjson)
- Health check: `curl http://<PI4_IP>:8787/health` should return `{ "ok": true }`
- Prep ESP32: `cd hardware/esp32_hands_mvp && cp config_template.h config.h` then edit Wi-Fi + BRAIN_HOST
- Flash ESP32: Open `esp32_hands_mvp.ino` in Arduino IDE (ESP32 Dev Module), upload, watch Serial at 115200
- Validate end-to-end: tail `logs/events.ndjson` on the Pi and confirm new entries every ~5 seconds
- Full details: see [docs/MVP_BRINGUP.md](docs/MVP_BRINGUP.md)

---

## Operating Modes

| Mode | Camera | AI Suggestions | HID Execution | Use Case |
|------|--------|----------------|---------------|----------|
| **Observe** | ✓ Active | ✗ Disabled | ✗ Disabled | Learning, monitoring |
| **Suggest** | ✓ Active | ✓ Enabled | ✗ Disabled | Evaluate AI suggestions |
| **Execute** | ✓ Active | ✓ Enabled | ✓ Approved actions only | Assisted workflows |

**Default mode**: Observe (safest)

---

## Core Safety Features

- ✅ **Physical kill switch** - Hardware power interrupt to HID executor
- ✅ **HID ARMED LED** - Visible indicator when execution enabled
- ✅ **Confirm-to-execute** - Every action requires explicit approval
- ✅ **Command bounds** - Max 1024 chars, rate limited (100ms)
- ✅ **Session logging** - Immutable audit trail of all actions
- ✅ **Smart brain, dumb hands** - AI logic separated from execution

---

## Documentation

### Quick Start

- [📦 **ChatGPT Context Pack**](docs/CHATGPT_CONTEXT_PACK.md) - **Complete repo context for AI assistants**

### Core Documents

- [📋 Project Charter](docs/00_PROJECT_CHARTER.md) - Goals, scope, and success criteria
- [📖 Project Overview](docs/00_PROJECT_OVERVIEW.md) - High-level introduction
- [🗂️ Repository Structure](docs/01_REPO_STRUCTURE.md) - Codebase organization
- [🏗️ System Architecture](docs/01_ARCHITECTURE.md) - Component design, data flows, diagrams

### Safety & Security

- [🛡️ Safety Guardrails](docs/02_SAFETY_GUARDRAILS.md) - Required safety mechanisms
- [📜 Action Protocol](docs/03_ACTION_PROTOCOL.md) - Approve/deny workflow
- [� **Contracts (v1)**](contracts/CONTRACTS_INDEX.md) - **JSON schema specifications for all messages**
- [�🔒 Threat Model](docs/10_THREAT_MODEL.md) - Security analysis and mitigations

### Hardware

- [🛒 Hardware BOM](docs/04_HARDWARE_BOM.md) - Bill of materials, sourcing, costs
- [🔧 Setup: HID Executor](docs/07_SETUP_HID_EXECUTOR.md) - Pico W firmware, wiring, kill switch

### Software Setup

- [💻 Setup: Brain VM](docs/05_SETUP_BRAIN_VM.md) - Proxmox VM, dependencies, AI models
- [📷 Setup: Camera](docs/06_SETUP_CAMERA.md) - Webcam/HDMI capture, OCR config

### Operations

- [🧪 Test Plans](docs/08_TEST_PLANS.md) - Unit, integration, safety, stress tests
- [📚 Runbooks](docs/09_RUNBOOKS.md) - Daily operations, troubleshooting, maintenance

---

## Design Principles (Non-Negotiable)

### 1. Smart Brain, Dumb Hands
- All reasoning happens in the Brain
- HID executor is a simple, bounded device
- No autonomous decision-making in HID firmware

### 2. Confirm-to-Execute by Default
- Observe-only and Suggest-only modes available
- Execute mode requires explicit approval for each action
- No batch execution without individual approvals

### 3. Full Visibility and Control
- Physical kill switch (hardware power interrupt)
- HID ARMED LED (visible indicator)
- Session logging (immutable audit trail)

### 4. Lab Safety First
- No payloads or exploits
- No bypassing OS security
- No privilege escalation
- No interaction with non-owned machines

---

## Hardware Components

### Required

| Component | Purpose | Notes |
|-----------|---------|-------|
| **Brain** | AI assistant, control logic | Raspberry Pi 4 or Proxmox VM |
| **HID Executor** | Keyboard/mouse actions | Raspberry Pi Pico W |
| **Camera** | Screen observation | USB webcam (1080p+) |
| **Kill Switch** | Emergency stop | SPST toggle, inline on VBUS |
| **HID ARMED LED** | Visual indicator | Red LED + 330Ω resistor |

### Optional

- E-ink status display (Pi Zero 2 W)
- HDMI capture device (better OCR)
- USB speaker (audio warnings)
- Network camera (wireless positioning)

**See [Hardware BOM](docs/04_HARDWARE_BOM.md) for complete list, part numbers, and sourcing.**

---

## Software Stack

### Brain
- **OS**: Ubuntu Server 22.04 LTS or Debian 12
- **AI**: Ollama (local LLM inference) - llama2:7b-chat or similar
- **Vision**: OpenCV + Tesseract OCR
- **UI**: Flask web interface (port 8080)
- **Language**: Python 3.11+

### HID Executor
- **Firmware**: CircuitPython 8.x
- **Libraries**: adafruit_hid
- **Language**: MicroPython/CircuitPython

### Target Systems
- Windows 10/11 VMs (primary)
- Linux VMs (Ubuntu, Debian)

---

## Project Status

✅ **Completed**:
- Core documentation and safety guardrails
- System architecture and design
- Hardware BOM and sourcing guide
- Setup guides for all components
- Comprehensive test plans
- Operational runbooks
- Threat model and security analysis

🚧 **In Progress**:
- Brain software implementation
- HID executor firmware
- Web UI development
- Integration testing

📋 **TODO**:
- Hardware assembly and wiring
- AI model fine-tuning for lab scenarios
- End-to-end integration tests
- Production deployment and training

---

## Development Workflow

### Repository Structure

```
hexforge-pla/
├── docs/              # All documentation (you are here)
├── hardware/          # Hardware designs, schematics
│   ├── eink-status-totem/
│   └── pico-hid-executor/
├── software/          # Software components
│   ├── brain/         # AI assistant, control logic
│   └── ui/            # Web interface
├── scripts/           # Helper scripts
│   ├── deploy/
│   └── dev/
└── logs/              # Development logs, notes
```

### Getting Started (Developers)

```bash
# Clone repository
git clone https://github.com/hexforge/hexforge-pla.git
cd hexforge-pla

# Read the docs (seriously, read them all)
cat docs/00_PROJECT_CHARTER.md
cat docs/02_SAFETY_GUARDRAILS.md

# Set up Brain development environment
cd software/brain
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests (when implemented)
pytest tests/

# Set up HID executor (requires Pico W)
# See docs/07_SETUP_HID_EXECUTOR.md
```

---

## Testing Requirements

**Before any deployment**:

- [ ] All Phase 1 unit tests pass (100%)
- [ ] **ALL Phase 2 safety tests pass (100%)** ← **CRITICAL**
- [ ] Phase 3 integration tests ≥95% pass
- [ ] Phase 4 stress tests ≥90% pass
- [ ] All Phase 5 security tests pass (100%)
- [ ] Kill switch verified by independent tester
- [ ] Operator training completed
- [ ] Lab supervisor sign-off

**See [Test Plans](docs/08_TEST_PLANS.md) for detailed procedures.**

---

## Authorized Use Policy

### ✅ Permitted Use

- Your own machines and devices
- Test VMs explicitly created for PLA testing
- Sandbox systems with no production data
- Lab training environments
- Demonstrations with informed consent

### ❌ Prohibited Use

- Coworker machines (without explicit written consent)
- Production systems
- Public or shared computers
- Systems containing regulated data (PII, PHI, PCI)
- **Any system you don't own or have explicit authorization to control**

**Violation of use policy may result in project suspension and disciplinary action.**

---

## Contributing

This is an **internal HexForge Labs project**. External contributions not accepted.

**Internal contributors**:
1. Read all documentation in `docs/` before making changes
2. All changes must preserve safety mechanisms (no bypassing kill switch, no auto-execute, etc.)
3. Run full test suite before committing
4. Update documentation for any behavior changes
5. Get code review from project lead before merging

---

## Support & Troubleshooting

- **Setup issues**: See individual setup guides in `docs/`
- **Operational issues**: See [Runbooks](docs/09_RUNBOOKS.md)
- **Safety incidents**: See [Runbooks - Emergency Procedures](docs/09_RUNBOOKS.md#emergency-procedures)
- **Security concerns**: See [Threat Model](docs/10_THREAT_MODEL.md)

**For critical safety issues**: Immediately stop operations, flip kill switch, and report to lab supervisor.

---

## License

**Internal use only. Not for distribution.**

Copyright © 2026 HexForge Labs. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

## Disclaimer

HexForge PLA is a powerful tool that executes keyboard and mouse actions on computer systems. 

**Operator responsibilities**:
- Understand all safety mechanisms before use
- Use only on authorized, operator-owned systems
- Never bypass safety features
- Maintain kill switch accessibility
- Follow all operational procedures
- Report all safety incidents

**HexForge Labs provides this tool "as-is" for internal lab use. Operator assumes all responsibility for safe and ethical use.**

---

**Questions? Read the docs. Still have questions? Read them again. 📚**
