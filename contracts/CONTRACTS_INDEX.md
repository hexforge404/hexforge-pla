# HexForge PLA Contracts Index (v1)

This index defines the contract set for the HexForge Portable Lab Assistant (PLA).
All contracts enforce safety bounds, operator approval workflows, and audit logging.

---

## Contract Philosophy

**Contract-First Design**: All communication between Brain and HID Executor uses validated JSON schemas.

**Safety-First**: Contracts enforce:
- Mode boundaries (OBSERVE/SUGGEST/EXECUTE)
- Command bounds (max 1024 chars, min 100ms delay)
- Required operator approval fields
- Mandatory session logging

**Internal-Only**: These contracts are for internal lab tool use only. Not for public APIs.

---

## HexForge Global Contracts (Ecosystem Alignment)

PLA aligns with HexForge's global contract standards for service interoperability:

### Job Status (`job_status.schema.json`)
**Scope**: Global - All HexForge engines/services  
**Purpose**: Canonical job status envelope for async operations  
**Required Fields**:
- `job_id` (string): Stable job identifier (filesystem-safe)
- `status` (enum): queued, running, complete, failed
- `service` (string): Engine/service name (e.g., "hexforge-pla")
- `updated_at` (string, ISO 8601): Last update timestamp
- Optional: `progress` (0.0-1.0), `message`, `error`, `result`

**PLA Usage**: When PLA runs as a service (e.g., batch automation jobs), it reports status using this schema.

### Job Manifest (`job_manifest.schema.json`)
**Scope**: Global - All HexForge engines/services  
**Purpose**: Canonical manifest for public assets produced by jobs  
**Required Fields**:
- `version` (enum): "v1"
- `job_id` (string): Stable job identifier
- `service` (string): Engine/service name
- `public_root` (string): Root folder (must start with `/assets/`)
- `public` (object): Asset references (all URLs must start with `/assets/`)

**PLA Usage**: PLA is primarily an internal tool and does not produce public assets. This schema is included for ecosystem consistency but not actively used in PLA v1.

---

## PLA-Specific Contracts (v1)

### 1. Action Proposal (`action_proposal.schema.json`)
**Direction**: Brain → Operator (via Web UI)  
**Purpose**: AI suggests an action based on observed screen state  
**Required Fields**:
- `proposal_id` (string): Unique identifier for tracking
- `timestamp` (string, ISO 8601): When proposal was generated
- `mode` (enum): Current system mode (OBSERVE, SUGGEST, EXECUTE)
- `action_type` (enum): TYPE_TEXT, KEY_COMBO, MOUSE_MOVE, MOUSE_CLICK
- `payload` (object): Action-specific parameters
- `rationale` (string): AI explanation for suggested action
- `credential_warning` (boolean): Flag if credentials detected
- `safety_bounds` (object): Enforced limits (max_chars, rate_limit_ms)

### 2. Action Decision (`action_decision.schema.json`)
**Direction**: Operator → Brain (via Web UI)  
**Purpose**: Operator approves or rejects proposed action  
**Required Fields**:
- `proposal_id` (string): Links to original proposal
- `decision` (enum): APPROVED, REJECTED
- `timestamp` (string, ISO 8601): When decision was made
- `operator_id` (string): Who made the decision
- `override_reason` (string, optional): If rejected, why

### 3. Action Execute (`action_execute.schema.json`)
**Direction**: Brain → HID Executor (via Serial)  
**Purpose**: Execute approved action with safety bounds  
**Required Fields**:
- `execution_id` (string): Unique identifier for this execution
- `proposal_id` (string): Links back to original proposal
- `timestamp` (string, ISO 8601): When execution was initiated
- `mode` (enum): Must be EXECUTE for HID actions
- `action_type` (enum): TYPE_TEXT, KEY_COMBO, MOUSE_MOVE, MOUSE_CLICK
- `payload` (object): Action-specific parameters (validated bounds)
- `safety_bounds` (object): max_text_length=1024, min_action_delay_ms=100

### 4. Session Log (`session_log.schema.json`)
**Direction**: Brain/HID Executor → Log Storage  
**Purpose**: Audit trail for all actions  
**Required Fields**:
- `log_id` (string): Unique log entry identifier
- `timestamp` (string, ISO 8601): When event occurred
- `event_type` (enum): PROPOSAL, DECISION, EXECUTION, ERROR, MODE_CHANGE
- `mode` (string): System mode at time of event
- `proposal_id` (string, optional): Links to proposal if applicable
- `execution_id` (string, optional): Links to execution if applicable
- `operator_id` (string): Who was responsible
- `details` (object): Event-specific data
- `checksum` (string): SHA256 hash for tamper detection

### 5. Device Status (`device_status.schema.json`)
**Direction**: HID Executor → Brain (via Serial)  
**Purpose**: Report HID executor health and safety state  
**Required Fields**:
- `device_id` (string): HID executor identifier
- `timestamp` (string, ISO 8601): Status report time
- `mode` (enum): Current mode (OBSERVE, SUGGEST, EXECUTE)
- `led_state` (boolean): HID ARMED LED status
- `kill_switch_state` (enum): ARMED, DISABLED, UNKNOWN
- `last_execution_time` (string, optional): Timestamp of last action
- `error_state` (object, optional): Current errors or warnings
- `uptime_seconds` (integer): Time since boot

---

## Contract Versioning Rules

**Version**: v1 (January 2026)

### Backward Compatibility
- Schemas are **append-only** within major version
- New optional fields may be added (existing fields remain required)
- Field types MUST NOT change within major version
- Enum values MUST NOT be removed within major version

### Breaking Changes (Major Version Bump)
- Removing required fields
- Changing field types
- Removing enum values
- Changing field semantics

### Version Transition
- Brain and HID Executor MUST validate contract version on startup
- Mismatched versions MUST log warning and refuse to execute HID actions
- Version is declared in schema `$schema` field

---

## Safety Guarantees

All contracts enforce these non-negotiable safety bounds:

| Bound | Value | Enforced By |
|-------|-------|-------------|
| `MAX_TEXT_LENGTH` | 1024 chars | Schema validation + HID executor |
| `MIN_ACTION_DELAY_MS` | 100 ms | HID executor firmware |
| `MODE_VALIDATION` | HID only in EXECUTE mode | Schema + executor |
| `OPERATOR_APPROVAL` | Required for all executions | Action decision contract |
| `SESSION_LOGGING` | All actions logged | Session log contract |
| `CREDENTIAL_WARNING` | Flag detected credentials | Action proposal contract |

---

## Implementation Notes

### Python Validation (Brain)
```python
import jsonschema
import json

# Load schema
with open('contracts/schemas/action_proposal.schema.json') as f:
    proposal_schema = json.load(f)

# Validate proposal
jsonschema.validate(proposal_data, proposal_schema)
```

### CircuitPython Validation (HID Executor)
**Note**: Full jsonschema not available in CircuitPython. Use lightweight validation:
```python
def validate_execute_command(cmd):
    required = ['execution_id', 'mode', 'action_type', 'payload']
    if not all(k in cmd for k in required):
        return False, "Missing required fields"
    if cmd['mode'] != 'EXECUTE':
        return False, "HID only in EXECUTE mode"
    # Validate payload bounds
    if cmd['action_type'] == 'TYPE_TEXT':
        if len(cmd['payload']['text']) > 1024:
            return False, "Text exceeds MAX_TEXT_LENGTH"
    return True, None
```

---

## Contract Violations

All violations MUST be logged and MUST prevent execution:

| Violation Type | Handling |
|----------------|----------|
| Schema validation failure | Log error, reject action, alert operator |
| Missing required field | Log error, return validation error response |
| Safety bound exceeded | Log error, reject action, alert operator |
| Mode mismatch | Log warning, disable HID, require mode reset |
| Missing operator approval | Log error, reject execution, require approval |

---

## Testing Requirements

Each schema MUST have:
- ✅ Valid fixture (passes validation)
- ✅ Invalid fixtures (missing fields, wrong types, bounds exceeded)
- ✅ Unit tests validating fixtures against schema
- ✅ Integration tests using contracts in Brain → HID flow

---

## References

- [Safety Guardrails](../docs/02_SAFETY_GUARDRAILS.md)
- [Action Protocol](../docs/03_ACTION_PROTOCOL.md)
- [Architecture](../docs/01_ARCHITECTURE.md)
- [Test Plans](../docs/08_TEST_PLANS.md)

---

**Contract Maintainer**: HexForge Team  
**Last Updated**: 2026-01-01  
**Version**: 1.0.0
