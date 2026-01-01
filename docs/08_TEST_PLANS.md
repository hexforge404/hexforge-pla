# Test Plans — HexForge PLA

**Purpose**: Comprehensive testing strategy to validate safety, functionality, and resilience.  
**Phases**: Component → Safety → Integration → Stress → Security

---

## Phase 1: Component Tests

### Camera & Vision System

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| CAM-001 | Detect USB camera at `/dev/video0` | Device enumerated, v4l2 reports capabilities |
| CAM-002 | Capture 1080p frame | Frame captured at 1920x1080, < 100ms latency |
| CAM-003 | OCR test on known text | Tesseract extracts text with >90% accuracy |
| CAM-004 | Handle camera disconnect | System logs error, degrades gracefully (no crash) |

### Brain AI System

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| AI-001 | Ollama model loads | `llama2:7b-chat` responds to test prompt |
| AI-002 | Suggest valid action from screen state | AI returns JSON action matching protocol |
| AI-003 | Detect credentials in OCR text | AI flags passwords/keys, refuses to type them |
| AI-004 | Reject ambiguous/unsafe commands | AI returns error for unclear or dangerous actions |

### HID Executor

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| HID-001 | Serial communication at 115200 baud | Commands sent/received with <10ms latency |
| HID-002 | Type text command | Text typed to target system exactly as sent |
| HID-003 | Mouse move command | Cursor moves to specified coordinates |
| HID-004 | Key combination (Ctrl+C) | Key combo executed atomically |
| HID-005 | LED indicator in EXECUTE mode | Red LED ON when mode=EXECUTE, OFF otherwise |

---

## Phase 2: Safety Mechanism Tests

### Kill Switch

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| SAFE-001 | Kill switch disables HID power | Toggling switch OFF powers down Pico W completely |
| SAFE-002 | Kill switch during HID action | Action stops mid-execution when switch toggled |
| SAFE-003 | Kill switch prevents reboot bypass | Pico W remains powered off until switch toggled ON |

### Command Bounds

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| SAFE-004 | Reject text > MAX_TEXT_LENGTH (1024) | Executor returns error, no text typed |
| SAFE-005 | Enforce rate limit (100ms) | Actions spaced ≥100ms apart even if sent faster |
| SAFE-006 | Reject invalid JSON | Executor returns parse error, ignores command |
| SAFE-007 | Reject commands in OBSERVE mode | Executor ignores HID commands unless mode=EXECUTE |

### Credential Protection

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| SAFE-008 | Detect AWS access key in OCR text | Brain flags `AKIA...` pattern, refuses to suggest typing |
| SAFE-009 | Detect SSH private key header | Brain flags `-----BEGIN PRIVATE KEY-----`, alerts operator |
| SAFE-010 | Detect password input field | Brain detects password field context, warns before typing |

---

## Phase 3: Integration Tests

### End-to-End Workflow

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| INT-001 | OBSERVE mode: Camera → AI → Suggestion | Brain captures screen, AI suggests action, no HID execution |
| INT-002 | SUGGEST mode: Operator approves action | Brain sends approved action to HID, executes successfully |
| INT-003 | EXECUTE mode: Autonomous action (manual approval) | Brain suggests, operator approves, HID executes, logs session |
| INT-004 | Mode transition: OBSERVE → SUGGEST → EXECUTE → OBSERVE | All mode changes recorded, HID state updates correctly |

### Error Handling

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| INT-005 | Camera failure during operation | Brain logs error, pauses suggestions, alerts operator |
| INT-006 | AI model crash/timeout | Brain retries AI query, falls back to OBSERVE mode |
| INT-007 | HID executor serial disconnect | Brain detects disconnect, disables EXECUTE mode, alerts operator |
| INT-008 | Target system unresponsive | HID executor timeout, Brain logs failure, suggests manual intervention |

---

## Phase 4: Stress Tests

### Performance Under Load

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| STRESS-001 | 100 consecutive HID commands | All commands execute with <5% failure rate |
| STRESS-002 | Rapid mode switching (10x/min for 30 min) | No crashes, all transitions logged |
| STRESS-003 | Long-running session (8 hours) | Memory usage stable, no memory leaks |
| STRESS-004 | OCR on complex screen (1000+ words) | Tesseract completes in <2 seconds |

### Boundary Conditions

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| STRESS-005 | Type 1024 character text (max length) | Entire text typed successfully |
| STRESS-006 | 1000 mouse moves in 2 minutes | Rate limiter enforces 100ms spacing, no dropped commands |
| STRESS-007 | AI prompt with 2000 token screen context | AI returns suggestion without truncation errors |

---

## Phase 5: Security Tests

### Attack Scenarios

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| SEC-001 | Prompt injection via OCR text | AI detects injection attempt, refuses to execute |
| SEC-002 | Malicious JSON command (code injection) | Executor rejects invalid JSON, logs attack attempt |
| SEC-003 | Credential exfiltration via keylogging | Session logs encrypted, keys not stored in plaintext |
| SEC-004 | Unauthorized mode escalation | Mode changes require operator approval, logged |
| SEC-005 | Firmware tampering (modified `main.py`) | Checksum validation fails, Pico W refuses to boot |

### Audit & Logging

| Test ID | Test Description | Pass Criteria |
|---------|------------------|---------------|
| SEC-006 | All HID actions logged | Every keystroke/mouse move recorded with timestamp |
| SEC-007 | Mode transitions logged | All OBSERVE/SUGGEST/EXECUTE changes logged with operator ID |
| SEC-008 | Session replay from logs | Logs contain enough detail to reconstruct actions |
| SEC-009 | Log tampering detection | Logs include checksums, tampering detectable |

---

## Test Execution Schedule

| Phase | Duration | Prerequisites | Owner |
|-------|----------|---------------|-------|
| Phase 1: Component | 2 days | Hardware assembled, firmware flashed | QA/Dev |
| Phase 2: Safety | 1 day | Phase 1 passed | QA |
| Phase 3: Integration | 3 days | Phase 1-2 passed | Dev/QA |
| Phase 4: Stress | 2 days | Phase 1-3 passed | QA |
| Phase 5: Security | 3 days | Phase 1-4 passed | Security Team |

**Total Estimated Time**: 11 days (2 weeks with buffer)

---

## Pass/Fail Criteria

### Phase Pass Requirements

- **Component Tests**: 100% pass rate (all critical systems functional)
- **Safety Tests**: 100% pass rate (zero tolerance for safety failures)
- **Integration Tests**: ≥95% pass rate (some flakiness acceptable, must re-test failures)
- **Stress Tests**: ≥90% pass rate (performance degradation acceptable, no crashes)
- **Security Tests**: 100% pass rate for critical scenarios (SEC-001 to SEC-005)

### Go/No-Go for Production Use

- ✅ All Phase 1-2 tests passed
- ✅ Kill switch validated by independent tester
- ✅ Credential detection working (SAFE-008, SAFE-009)
- ✅ Session logging functional (SEC-006 to SEC-009)
- ✅ Integration tests passed with <5% failure rate
- ✅ Operator training completed
- ✅ Runbooks reviewed and approved

**If any above criteria are not met: DO NOT DEPLOY TO PRODUCTION.**

---

**See also**:
- [Safety Guardrails](02_SAFETY_GUARDRAILS.md)
- [Runbooks: Troubleshooting](09_RUNBOOKS.md)
- [Threat Model](10_THREAT_MODEL.md)
