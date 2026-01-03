# HexForge PLA - ChatGPT Context Pack

**Repository**: hexforge-pla  
**Version**: v1.0.0  
**Last Updated**: 2026-01-01  
**Status**: Contract system complete, Brain/UI integration pending

---

## What HexForge PLA Is

**Portable Lab Assistant**: An internal lab tool combining camera vision ("eyes"), AI reasoning ("brain"), and bounded HID execution ("hands") with strict confirm-to-execute guardrails.

**Architecture**: "Smart Brain, Dumb Hands"
- **Brain** (Proxmox VM): AI vision, reasoning, proposal generation, operator interface
- **HID Executor** (Raspberry Pi Pico W): Bounded keyboard/mouse executor with physical kill switch
- **Camera** (USB webcam): Screen capture and OCR for context awareness
- **Status Display** (Optional e-ink): Real-time mode/status indicator

**Safety-First Design**:
- Physical kill switch (hardware power interrupt to HID)
- Visible "HID ARMED" LED indicator
- Confirm-to-execute: Every action requires explicit operator approval
- Command bounds: max 1024 chars, rate limited (100ms minimum delay)
- Immutable session logging with checksums
- No autonomous decision-making in HID firmware

---

## What HexForge PLA Is NOT

- ❌ NOT autonomous (operator approval required for every action)
- ❌ NOT for use on non-owned systems
- ❌ NOT a payload delivery system or exploit tool
- ❌ NOT designed for privilege escalation or security bypassing
- ❌ NOT for production/customer-facing environments
- ❌ NOT stealthy (visible LED, logged sessions)

---

## Current Repository State

### Implemented (Production Ready)

**Contract System (v1.0.0)**: ✅ COMPLETE
- 7 JSON schemas (5 PLA-specific + 2 HexForge global)
- Full jsonschema validation (Brain: Python 3.11+)
- Lightweight validation (HID Executor: CircuitPython)
- 15/15 contract validation tests passing
- Comprehensive documentation (5 files, 1000+ lines)

**HID Executor Firmware**: ✅ FUNCTIONAL (337 lines)
- Contract validation integrated
- Mode state machine (OBSERVE/SUGGEST/EXECUTE)
- Safety bounds enforcement (max text, rate limiting)
- LED indicator (ON when EXECUTE mode)
- Serial communication (115200 baud)
- Legacy protocol support (backward compatible)

**Documentation**: ✅ COMPREHENSIVE (13 files)
- System architecture with diagrams
- Safety guardrails and threat model
- Hardware BOM and setup guides
- Test plans and runbooks
- Contract specifications and mappings

### Partially Implemented (Scaffolding)

**Brain Main Loop** (115 lines): 🚧 SCAFFOLDING
- Logging infrastructure complete
- Signal handling complete
- Main event loop: TODO (camera → AI → proposals → execution)
- Component integration: Placeholder code only

**Test Suite**: 🚧 MIXED
- Contract tests: ✅ 15/15 passing
- Camera tests: 🚧 Integration test framework (not unit tests)
- HID tests: 🚧 Integration test framework (not unit tests)
- Safety tests: ❌ NOT IMPLEMENTED
- Stress tests: ❌ NOT IMPLEMENTED

**Web UI**: ❌ NOT STARTED
- No control panel implementation
- No proposal approval interface
- No session log viewer

### Not Started

- AI vision pipeline (screen analysis, OCR integration)
- AI reasoning engine (action proposals, rationale generation)
- Camera capture module (frame grabbing, OCR)
- Mode manager (state machine coordination)
- Session logger (audit trail with checksums)
- E-ink status display integration
- End-to-end integration tests

---

## Contract System (v1.0.0)

### All Schemas (7 total)

**PLA-Specific Contracts** (Internal Communication):

1. **action_proposal.schema.json** (Brain → Operator)
   - Purpose: AI suggests action based on screen state
   - Required: proposal_id, timestamp, mode, action_type, payload, rationale, credential_warning, safety_bounds
   - Enforces: credential_warning flag, max_text_length=1024

2. **action_decision.schema.json** (Operator → Brain)
   - Purpose: Operator approves/rejects proposal
   - Required: decision_id, timestamp, proposal_id, decision
   - Enforces: APPROVED/REJECTED enum, operator_id tracking

3. **action_execute.schema.json** (Brain → HID Executor)
   - Purpose: Execute approved action
   - Required: command_id, timestamp, mode, action_type, payload, operator_approval, safety_bounds
   - Enforces: mode="EXECUTE" (const), operator approval required, safety bounds

4. **session_log.schema.json** (All Events → Audit Log)
   - Purpose: Immutable audit trail
   - Required: log_id, timestamp, event_type, actor, event_data, session_id, checksum
   - Enforces: checksum for tamper detection, event_type enum

5. **device_status.schema.json** (HID Executor → Brain)
   - Purpose: HID status reporting
   - Required: device_id, timestamp, mode, led_state, kill_switch_state, last_command_id
   - Enforces: kill_switch_state (ARMED/SAFE), led_state reporting

**HexForge Global Contracts** (Ecosystem Alignment):

6. **job_status.schema.json** (Global: All HexForge Services)
   - Purpose: Canonical job status envelope for async operations
   - Required: job_id, status, service, updated_at
   - Status enum: queued, running, complete, failed
   - PLA usage: When PLA runs as batch automation service (future v1.1.0)
   - Optional: progress (0.0-1.0), message, error, result

7. **job_manifest.schema.json** (Global: All HexForge Services)
   - Purpose: Public asset manifest
   - Required: version, job_id, service, public_root (must start with /assets/)
   - PLA usage: Currently NONE (PLA is internal tool, no public assets). Included for ecosystem consistency.

### Safety Guarantees Enforced by Contracts

| Guarantee | Enforced By | Mechanism |
|-----------|-------------|-----------|
| Max text length (1024 chars) | Schema + HID executor | `safety_bounds.max_text_length` validation + firmware check |
| Rate limiting (100ms min) | HID executor firmware | `safety_bounds.min_action_delay_ms` + enforce_rate_limit() |
| Mode validation | Schema + HID executor | `mode: "EXECUTE"` const in schema, HID checks mode |
| Operator approval | Schema enforcement | `operator_approval.operator_id` required field |
| Credential warning | Schema enforcement | `credential_warning: boolean` required field |
| Session logging | Schema enforcement | `session_log.checksum` required for audit trail |
| Kill switch state | Schema enforcement | `device_status.kill_switch_state` required reporting |

### Validation Infrastructure

**Brain Validator** (`software/brain/src/contract_validator.py`, 225 lines):
- Language: Python 3.11+
- Library: jsonschema 4.20.0
- Features: Validates all 7 contracts, singleton pattern, detailed error reporting
- Methods:
  - `validate_proposal(data)` → (bool, error_msg)
  - `validate_decision(data)` → (bool, error_msg)
  - `validate_execute(data)` → (bool, error_msg)
  - `validate_session_log(data)` → (bool, error_msg)
  - `validate_device_status(data)` → (bool, error_msg)
  - `validate_job_status(data)` → (bool, error_msg)
  - `validate_job_manifest(data)` → (bool, error_msg)

**HID Validator** (`hardware/pico-hid-executor/contract_validator.py`, 130 lines):
- Language: CircuitPython (MicroPython)
- Library: Pure Python (no jsonschema, size constraints)
- Features: Lightweight validation, graceful error messages
- Functions:
  - `validate_execute_command(data)` → (bool, error_msg)
  - `validate_device_status(data)` → (bool, error_msg)
- Validates: Required fields, types, enums, safety bounds
- Does NOT validate: Global contracts (HID executor is not a service)

**Test Results**: 15/15 tests passing ✅

Test breakdown:
- Valid proposals: 3/3 ✅
- Valid decisions: 2/2 ✅
- Valid execute commands: 1/1 ✅
- Invalid commands: 3/3 ✅ (correctly rejected)
- Session logs: 1/1 ✅
- Device status: 1/1 ✅
- Global job_status: 4/4 ✅

Run tests:
```bash
cd /mnt/hdd-storage/hexforge-pla
python3 software/brain/tests/test_contracts.py
# Expected: 15/15 tests passed 🎉
```

---

## System Architecture

### Trust Boundaries

```
┌─────────────────────────────────────────────┐
│  OPERATOR CONTROL LAYER                     │
│  - Physical kill switch                     │
│  - Approve/deny interface                   │
│  - Session monitoring                       │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  TRUSTED ZONE (Brain)                       │
│  - Vision → Analysis → Reasoning            │
│  - Proposal generation                      │
│  - NO direct HID access                     │
└─────────────────────────────────────────────┘
                     │
            (Approval Gate)
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  CONSTRAINED ZONE (HID Executor)            │
│  - Dumb HID executor                        │
│  - Bounded commands only                    │
│  - Rate limited                             │
│  - Kill switch interrupt                    │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  TARGET SYSTEM (Sandbox)                    │
│  - Test VM (Windows/Linux)                  │
│  - Operator-owned machines only             │
└─────────────────────────────────────────────┘
```

### Component Status

**Camera (USB Webcam)**:
- Status: Test framework exists, no production code
- Expected: v4l2 device at /dev/video0, 1080p capture
- Integration: TODO (capture loop not implemented)

**Vision Pipeline**:
- Status: NOT STARTED
- Expected: OpenCV frame capture, Tesseract OCR
- Integration: TODO (no AI vision module)

**AI Engine**:
- Status: NOT STARTED
- Expected: Ollama (llama2:7b-chat), action proposals with rationale
- Integration: TODO (no reasoning engine)

**Brain Main Loop** (`software/brain/src/main.py`, 115 lines):
- Status: SCAFFOLDING
- Implemented: Logging, signal handling, placeholder config
- TODO: Camera capture loop, AI integration, proposal generation, HID interface

**HID Executor** (`hardware/pico-hid-executor/main.py`, 337 lines):
- Status: FUNCTIONAL ✅
- Implemented: Contract validation, mode state machine, safety bounds, LED indicator
- Protocol: JSON commands via USB serial (115200 baud)
- Legacy support: Backward compatible with pre-contract protocol

**Web UI**:
- Status: NOT STARTED
- Expected: Flask/FastAPI control panel, proposal approval interface, session log viewer
- Integration: TODO (no UI implementation)

**Session Logger**:
- Status: NOT STARTED
- Expected: Immutable log file with checksums, contract-compliant entries
- Integration: TODO (no logging module)

**E-ink Status Display**:
- Status: OPTIONAL, NOT STARTED
- Expected: Real-time mode/status indicator on e-ink screen

---

## Operating Modes

| Mode | Camera | AI Suggestions | HID Execution | Use Case |
|------|--------|----------------|---------------|----------|
| **OBSERVE** | ✓ Active | ✗ Disabled | ✗ Disabled | Learning, monitoring (safest) |
| **SUGGEST** | ✓ Active | ✓ Enabled | ✗ Disabled | Evaluate AI suggestions |
| **EXECUTE** | ✓ Active | ✓ Enabled | ✓ Approved only | Assisted workflows |

**Default**: OBSERVE (system always starts in safest mode)

**Mode Transitions**:
- OBSERVE → SUGGEST: Enable AI suggestions (operator controlled)
- SUGGEST → EXECUTE: Enable HID execution (requires kill switch ON + LED indicator)
- Any mode → OBSERVE: Emergency fallback (kill switch OFF forces OBSERVE)

---

## Safety Posture

### Physical Safety Mechanisms

1. **Kill Switch** (Hardware)
   - Type: VBUS interrupt (cannot be bypassed in firmware)
   - Effect: Removes power to Raspberry Pi Pico W completely
   - Location: Inline with USB power to HID executor
   - Test: SAFE-001, SAFE-002, SAFE-003 (not yet implemented)

2. **HID ARMED LED** (Visible Indicator)
   - Color: Red
   - State: ON when mode=EXECUTE, OFF otherwise
   - Location: GPIO 2 on Pico W
   - Purpose: Operator always knows when HID can execute

3. **Mode State Machine**
   - Default: OBSERVE (no HID execution)
   - Explicit transitions required
   - Cannot bypass OBSERVE → EXECUTE directly

### Software Safety Mechanisms

1. **Contract Validation** (All Messages)
   - Brain validates proposals before sending to operator
   - Brain validates decisions before executing
   - HID validates execute commands before processing
   - Invalid contracts rejected with clear error messages

2. **Command Bounds** (Enforced by HID Firmware)
   - MAX_TEXT_LENGTH: 1024 characters
   - MIN_ACTION_DELAY_MS: 100 milliseconds
   - Firmware rejects oversized/too-fast commands

3. **Operator Approval Gate** (Every Action)
   - No batch execution without per-action approval
   - Operator ID tracked in contracts
   - Rejection reasons logged

4. **Session Logging** (Immutable Audit Trail)
   - All events logged with checksums
   - Tamper detection via checksum chain
   - Operator-readable log files

5. **Credential Detection** (Schema Enforcement)
   - `credential_warning` flag required in proposals
   - AI must flag passwords/keys before proposing typing
   - Operator explicitly warned when credentials involved

---

## File Structure

```
hexforge-pla/
├── contracts/                              # Contract system (v1.0.0) ✅
│   ├── schemas/
│   │   ├── action_proposal.schema.json     (PLA-specific)
│   │   ├── action_decision.schema.json     (PLA-specific)
│   │   ├── action_execute.schema.json      (PLA-specific)
│   │   ├── session_log.schema.json         (PLA-specific)
│   │   ├── device_status.schema.json       (PLA-specific)
│   │   ├── job_status.schema.json          (HexForge global)
│   │   └── job_manifest.schema.json        (HexForge global)
│   ├── CONTRACTS_INDEX.md                  (225 lines - complete specs)
│   ├── GLOBAL_CONTRACT_MAPPING.md          (200+ lines - PLA↔global mapping)
│   ├── IMPLEMENTATION_SUMMARY.md           (300+ lines - integration guide)
│   ├── CHANGELOG.md                        (version history)
│   └── GLOBAL_INTEGRATION_STATUS.md        (integration summary)
│
├── docs/                                   # Documentation (13 files) ✅
│   ├── 00_PROJECT_CHARTER.md               (goals, non-goals, success criteria)
│   ├── 00_PROJECT_OVERVIEW.md              (high-level intro)
│   ├── 01_ARCHITECTURE.md                  (428 lines - diagrams, data flows)
│   ├── 01_REPO_STRUCTURE.md                (codebase organization)
│   ├── 02_SAFETY_GUARDRAILS.md             (required safety mechanisms)
│   ├── 03_ACTION_PROTOCOL.md               (approve/deny workflow)
│   ├── 04_HARDWARE_BOM.md                  (parts list, costs)
│   ├── 05_SETUP_BRAIN_VM.md                (Proxmox VM, dependencies)
│   ├── 06_SETUP_CAMERA.md                  (webcam/HDMI capture)
│   ├── 07_SETUP_HID_EXECUTOR.md            (Pico W firmware, wiring)
│   ├── 08_TEST_PLANS.md                    (test strategy)
│   ├── 09_RUNBOOKS.md                      (operations, troubleshooting)
│   └── 10_THREAT_MODEL.md                  (security analysis)
│
├── hardware/
│   └── pico-hid-executor/                  # HID Executor (functional) ✅
│       ├── main.py                         (337 lines - firmware)
│       ├── contract_validator.py           (130 lines - validation)
│       └── README.md                       (setup instructions)
│
├── software/
│   └── brain/                              # Brain system (scaffolding) 🚧
│       ├── src/
│       │   ├── main.py                     (115 lines - scaffolding)
│       │   └── contract_validator.py       (225 lines - complete)
│       ├── tests/
│       │   ├── fixtures/                   (13 JSON files)
│       │   ├── test_contracts.py           (15/15 tests passing ✅)
│       │   ├── test_camera.py              (integration framework)
│       │   └── test_hid_executor.py        (integration framework)
│       ├── requirements.txt                (jsonschema==4.20.0, etc.)
│       └── README.md
│
└── README.md                               (main entry point)
```

---

## Testing Summary

### Contract Validation Tests (15/15 passing)

**Test Suite**: `software/brain/tests/test_contracts.py`

**Coverage**:
- PLA proposals: 3 valid scenarios + 2 invalid (missing field, text too long)
- PLA decisions: 2 valid scenarios (approved, rejected)
- PLA execute: 1 valid scenario + 1 invalid (wrong mode)
- Session logs: 1 valid scenario
- Device status: 1 valid scenario
- Global job_status: 3 valid scenarios (running, complete, failed) + 1 invalid (wrong enum)

**Test Fixtures**: 13 JSON files (9 valid + 4 invalid)

**Run Command**:
```bash
cd /mnt/hdd-storage/hexforge-pla
python3 software/brain/tests/test_contracts.py
```

**Expected Output**: `15/15 tests passed 🎉`

### Integration Tests (Scaffolding Only)

**Camera Tests** (`test_camera.py`):
- Camera detection (/dev/video0)
- Frame capture (1080p)
- OCR text extraction
- Camera disconnect handling
- Status: Framework exists, requires actual hardware

**HID Tests** (`test_hid_executor.py`):
- Serial communication (115200 baud)
- Mode transitions (OBSERVE/SUGGEST/EXECUTE)
- Type text command
- Key combination execution
- Safety bounds enforcement
- Status: Framework exists, requires HID device connected

### Missing Tests

- ❌ Safety mechanism tests (kill switch, LED, bounds)
- ❌ AI engine tests (proposals, rationale, credential detection)
- ❌ Vision pipeline tests (OCR, screen analysis)
- ❌ End-to-end integration tests
- ❌ Stress tests (rate limiting, long sessions)
- ❌ Security tests (threat model validation)

---

## Key Design Decisions

1. **Contract-First Architecture**
   - All messages validated against JSON schemas
   - Safety bounds enforced at schema level
   - Enables clear specification and testing

2. **Smart Brain, Dumb Hands**
   - All reasoning in Brain (trusted zone)
   - HID executor is simple bounded device
   - No autonomous decision-making in firmware

3. **Physical Kill Switch**
   - Hardware interrupt (cannot be bypassed)
   - Forces OBSERVE mode when OFF
   - Visible LED indicator

4. **Confirm-to-Execute Default**
   - System starts in OBSERVE mode (safest)
   - Every action requires explicit approval
   - No batch execution without per-action approval

5. **HexForge Ecosystem Alignment**
   - Global contracts (job_status, job_manifest) included
   - PLA can participate in HexForge monitoring (future)
   - Currently internal-only tool (no public assets)

---

## Next Work (Priority Order)

### Critical Path (MVP Completion)

1. **Brain Camera Module** (`software/brain/src/camera.py`)
   - OpenCV capture from /dev/video0
   - Tesseract OCR integration
   - Frame preprocessing and text extraction
   - Estimated: 200-300 lines

2. **Brain AI Engine** (`software/brain/src/ai_engine.py`)
   - Ollama integration (llama2:7b-chat)
   - Screen state analysis → action proposals
   - Credential detection (passwords/keys)
   - Proposal generation with rationale
   - Estimated: 300-400 lines

3. **Web UI - Control Panel** (`software/brain/ui/`)
   - Flask/FastAPI server
   - Proposal approval/denial interface
   - Session log viewer
   - Mode switcher (OBSERVE/SUGGEST/EXECUTE)
   - Estimated: 500-700 lines

4. **Brain Main Loop Integration** (`software/brain/src/main.py`)
   - Wire camera → vision → AI → proposals
   - Integrate contract validation
   - Handle operator decisions
   - Execute approved actions via HID
   - Estimated: Update from 115 → 300+ lines

5. **Session Logger** (`software/brain/src/session_logger.py`)
   - Immutable log file writer
   - Checksum calculation for tamper detection
   - Contract-compliant log entries
   - Estimated: 150-200 lines

### Important (Safety & Testing)

6. **Safety Mechanism Tests** (`software/brain/tests/test_safety.py`)
   - Kill switch tests (SAFE-001, SAFE-002, SAFE-003)
   - Command bounds tests (BOUND-001, BOUND-002, BOUND-003)
   - Mode validation tests (MODE-001, MODE-002)
   - LED indicator tests
   - Estimated: 200-300 lines

7. **End-to-End Integration Test** (`software/brain/tests/test_e2e.py`)
   - Full workflow: camera → AI → proposal → approval → HID → log
   - Test with actual target VM
   - Validate session log integrity
   - Estimated: 300-400 lines

### Nice-to-Have (Post-MVP)

8. **Mode Manager** (`software/brain/src/mode_manager.py`)
   - State machine for mode transitions
   - Mode change validation
   - Event broadcasting
   - Estimated: 100-150 lines

9. **E-ink Status Display** (Optional)
   - Real-time mode/status indicator
   - I2C/SPI integration
   - Status update loop
   - Estimated: 150-200 lines

10. **Service Mode** (v1.1.0)
    - Batch automation capability
    - job_status reporting to HexForge ecosystem
    - Headless operation support
    - Estimated: 200-300 lines

---

## Key Files to Review

**Contracts** (Start Here):
- [contracts/CONTRACTS_INDEX.md](../contracts/CONTRACTS_INDEX.md) - Complete contract specifications
- [contracts/GLOBAL_CONTRACT_MAPPING.md](../contracts/GLOBAL_CONTRACT_MAPPING.md) - PLA ↔ global contract mapping

**System Design**:
- [docs/01_ARCHITECTURE.md](01_ARCHITECTURE.md) - Architecture diagrams, trust boundaries, data flows
- [docs/02_SAFETY_GUARDRAILS.md](02_SAFETY_GUARDRAILS.md) - Safety requirements

**Implementation**:
- [software/brain/src/contract_validator.py](../software/brain/src/contract_validator.py) - Brain validator (225 lines)
- [hardware/pico-hid-executor/main.py](../hardware/pico-hid-executor/main.py) - HID firmware (337 lines)
- [software/brain/tests/test_contracts.py](../software/brain/tests/test_contracts.py) - Contract tests (15/15 passing)

**Operations**:
- [docs/09_RUNBOOKS.md](09_RUNBOOKS.md) - Daily operations, troubleshooting
- [docs/08_TEST_PLANS.md](08_TEST_PLANS.md) - Comprehensive test strategy

---

## Common Commands

**Run Contract Tests**:
```bash
cd /mnt/hdd-storage/hexforge-pla
python3 software/brain/tests/test_contracts.py
# Expected: 15/15 tests passed
```

**Test Camera (Requires Hardware)**:
```bash
python3 software/brain/tests/test_camera.py
```

**Test HID Executor (Requires Hardware)**:
```bash
python3 software/brain/tests/test_hid_executor.py
```

**Validate Contract File**:
```bash
python3 -c "
from software.brain.src.contract_validator import validate_proposal
import json
with open('software/brain/tests/fixtures/valid_proposal_type_text.json') as f:
    data = json.load(f)
is_valid, error = validate_proposal(data)
print('Valid!' if is_valid else f'Error: {error}')
"
```

---

## Project Status Summary

**Contract System**: ✅ Production ready (v1.0.0)
- All schemas defined and validated
- Validators implemented and tested
- Documentation comprehensive

**HID Executor**: ✅ Functional
- Firmware complete with safety bounds
- Contract validation integrated
- LED indicator working

**Brain System**: 🚧 Scaffolding only
- Main loop placeholder
- Camera module: NOT STARTED
- AI engine: NOT STARTED
- Web UI: NOT STARTED
- Session logger: NOT STARTED

**Testing**: 🚧 Partial
- Contract tests: 15/15 passing ✅
- Integration tests: Framework only
- Safety tests: NOT IMPLEMENTED
- E2E tests: NOT IMPLEMENTED

**Documentation**: ✅ Comprehensive
- 13 docs covering all aspects
- Diagrams and workflows included
- Setup guides complete

**MVP Status**: ~30% complete
- Contracts and specs: 100% ✅
- HID executor: 100% ✅
- Brain implementation: 10% 🚧
- UI: 0% ❌
- Testing: 30% 🚧

---

**Last Updated**: 2026-01-01  
**Next Review**: After Brain camera/AI modules implemented  
**Contact**: HexForge Team (internal use only)
