# Repository Structure — HexForge PLA

**Last Updated**: 2026-01-01

---

## Directory Tree

```
hexforge-pla/
├── README.md                           # Main project readme
│
├── docs/                               # All documentation
│   ├── 00_PROJECT_CHARTER.md          # Goals, scope, success criteria
│   ├── 00_PROJECT_OVERVIEW.md         # High-level introduction
│   ├── 01_ARCHITECTURE.md             # System architecture, diagrams
│   ├── 01_REPO_STRUCTURE.md           # This file
│   ├── 02_SAFETY_GUARDRAILS.md        # Safety requirements
│   ├── 03_ACTION_PROTOCOL.md          # Approve/deny workflow
│   ├── 04_HARDWARE_BOM.md             # Bill of materials
│   ├── 05_SETUP_BRAIN_VM.md           # Brain system setup
│   ├── 06_SETUP_CAMERA.md             # Camera/vision setup
│   ├── 07_SETUP_HID_EXECUTOR.md       # HID executor firmware setup
│   ├── 08_TEST_PLANS.md               # Comprehensive test plans
│   ├── 09_RUNBOOKS.md                 # Operations and troubleshooting
│   └── 10_THREAT_MODEL.md             # Security analysis
│
├── hardware/                           # Hardware designs and firmware
│   ├── eink-status-totem/             # Optional status display
│   │   └── (future: firmware, wiring diagrams)
│   │
│   └── pico-hid-executor/             # HID executor (Pico W)
│       ├── README.md                  # Setup instructions
│       └── main.py                    # CircuitPython firmware
│
├── software/                           # Software components
│   ├── brain/                         # Brain AI assistant
│   │   ├── README.md                  # Setup and development
│   │   ├── requirements.txt           # Python dependencies
│   │   ├── config.example.yaml        # Configuration template
│   │   ├── test_camera.py             # Camera test utility
│   │   ├── test_ocr.py                # OCR test utility
│   │   ├── src/                       # Source code (future)
│   │   │   └── main.py                # Entry point (scaffold)
│   │   └── tests/                     # Unit tests (future)
│   │
│   └── ui/                             # Web UI (future)
│       └── (future: Flask/React interface)
│
├── config/                             # Configuration files (gitignored)
│   └── brain_config.yaml              # Runtime configuration (create from template)
│
├── scripts/                            # Helper scripts
│   ├── deploy/                        # Deployment automation (future)
│   └── dev/                           # Development utilities (future)
│
└── logs/                               # Development logs (gitignored)
    └── (session logs, debug outputs)
```

---

## File Purposes

### Documentation (`docs/`)

| File | Purpose | Audience |
|------|---------|----------|
| 00_PROJECT_CHARTER.md | Project goals, scope, success criteria | All team members |
| 00_PROJECT_OVERVIEW.md | High-level introduction | New team members |
| 01_ARCHITECTURE.md | System design, component diagrams | Developers, reviewers |
| 01_REPO_STRUCTURE.md | This file - repository organization | All contributors |
| 02_SAFETY_GUARDRAILS.md | Safety requirements and controls | All team members |
| 03_ACTION_PROTOCOL.md | Command approval workflow | Operators, developers |
| 04_HARDWARE_BOM.md | Parts list, sourcing, costs | Hardware builders |
| 05_SETUP_BRAIN_VM.md | Brain system installation | System administrators |
| 06_SETUP_CAMERA.md | Vision pipeline setup | System administrators |
| 07_SETUP_HID_EXECUTOR.md | HID executor firmware setup | Hardware builders |
| 08_TEST_PLANS.md | Comprehensive test procedures | QA, operators |
| 09_RUNBOOKS.md | Daily operations, troubleshooting | Operators |
| 10_THREAT_MODEL.md | Security analysis, mitigations | Security reviewers, PM |

---

## Getting Started (Quick Reference)

### For Operators
1. Read [Project Charter](00_PROJECT_CHARTER.md)
2. Read [Safety Guardrails](02_SAFETY_GUARDRAILS.md)
3. Read [Runbooks](09_RUNBOOKS.md)

### For Developers
1. Read [Architecture](01_ARCHITECTURE.md)
2. Read [Threat Model](10_THREAT_MODEL.md)
3. Set up development environment: `software/brain/README.md`

### For Hardware Builders
1. Read [Hardware BOM](04_HARDWARE_BOM.md)
2. Follow [Setup: HID Executor](07_SETUP_HID_EXECUTOR.md)
3. Follow [Setup: Brain VM](05_SETUP_BRAIN_VM.md)
4. Follow [Setup: Camera](06_SETUP_CAMERA.md)

---

## Development Status

### ✅ Completed
- Comprehensive documentation (10+ docs)
- System architecture and diagrams
- Hardware BOM and sourcing
- HID executor firmware scaffold
- Brain software scaffold
- Test plans and procedures
- Operational runbooks
- Threat model and security analysis

### 🚧 In Progress
- Brain AI core implementation
- Vision pipeline implementation
- Web UI development

### 📋 TODO
- Hardware assembly and wiring
- Integration testing
- AI model fine-tuning
- End-to-end testing
- Production deployment

---

**See [README.md](../README.md) for full project overview.**
