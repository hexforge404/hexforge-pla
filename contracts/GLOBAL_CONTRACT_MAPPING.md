# HexForge PLA ↔ Global Contract Mapping

**Purpose**: Document how PLA's internal contracts relate to HexForge's global ecosystem contracts.

---

## Contract Hierarchy

```
HexForge Ecosystem (Global)
├── job_status.schema.json     ← All services MUST use
├── job_manifest.schema.json   ← All services MUST use
│
└── HexForge PLA (Internal)
    ├── action_proposal.schema.json     ← PLA-specific (Brain → Operator)
    ├── action_decision.schema.json     ← PLA-specific (Operator → Brain)
    ├── action_execute.schema.json      ← PLA-specific (Brain → HID)
    ├── session_log.schema.json         ← PLA-specific (audit logging)
    └── device_status.schema.json       ← PLA-specific (HID → Brain)
```

---

## Mapping: PLA Session → HexForge Job

When PLA runs as a batch automation service (not interactive mode), it can report status using the global job_status schema:

### PLA Session Log Entry → Job Status

| PLA Contract | Global Contract | Mapping |
|--------------|-----------------|---------|
| `session_log.log_id` | `job_status.job_id` | Direct mapping |
| `session_log.event_type` | `job_status.status` | `PROPOSAL`/`DECISION` → `running`, `EXECUTION` → `running`, completion → `complete`, `ERROR` → `failed` |
| N/A (PLA runs on Brain) | `job_status.service` | Fixed: `"hexforge-pla"` |
| `session_log.timestamp` | `job_status.updated_at` | Direct mapping (ISO 8601) |
| N/A (optional for PLA) | `job_status.progress` | Could track: actions_completed / total_actions |
| `session_log.details` | `job_status.message` | Human-readable summary |
| `session_log.details.error_message` | `job_status.error.detail` | If event_type=ERROR |

### Example Mapping

**PLA Session Log Entry**:
```json
{
  "log_id": "session_20260101_103045",
  "timestamp": "2026-01-01T10:30:45Z",
  "event_type": "EXECUTION",
  "mode": "EXECUTE",
  "operator_id": "operator_alice",
  "execution_id": "exec_99887766_aabbcc",
  "details": {
    "action_type": "TYPE_TEXT",
    "payload_summary": "Typed 'testuser123' into login field"
  },
  "checksum": "a1b2c3d4..."
}
```

**Equivalent Job Status**:
```json
{
  "job_id": "session_20260101_103045",
  "status": "running",
  "service": "hexforge-pla",
  "updated_at": "2026-01-01T10:30:45Z",
  "progress": 0.6,
  "message": "Executing action: TYPE_TEXT - Typed 'testuser123' into login field"
}
```

---

## When to Use Which Contract

### Use PLA-Specific Contracts (Always)
- **Internal operations**: All Brain ↔ HID Executor communication
- **Operator interface**: All Web UI interactions
- **Audit logging**: All session logs for compliance

### Use Global Contracts (When Applicable)
- **Service reporting**: If PLA exposes an API for external monitoring
- **Integration with HexForge dashboard**: If PLA status appears in central monitoring
- **Batch automation mode**: If PLA runs scheduled jobs (future feature)

---

## PLA Does NOT Use job_manifest.schema.json

**Reason**: PLA is an internal tool that:
- Does NOT produce public assets under `/assets/`
- Does NOT generate 3D models, textures, or previews
- Produces only session logs (internal audit trail)

**Exception**: If future PLA versions add screenshot/video recording features, those could be published as:
```json
{
  "version": "v1",
  "job_id": "session_20260101_103045",
  "service": "hexforge-pla",
  "updated_at": "2026-01-01T10:35:00Z",
  "subfolder": null,
  "public_root": "/assets/pla-sessions/",
  "public": {
    "job_json": "/assets/pla-sessions/session_20260101_103045.json",
    "session_recording": {
      "video": "/assets/pla-sessions/session_20260101_103045.mp4",
      "screenshots": "/assets/pla-sessions/screenshots/"
    }
  }
}
```

---

## Contract Validation Strategy

### Brain Validator (`software/brain/src/contract_validator.py`)
```python
# Supports BOTH PLA-specific and global contracts

from contract_validator import get_validator

validator = get_validator()

# Validate PLA-specific contracts
is_valid, error = validator.validate_proposal(proposal_data)
is_valid, error = validator.validate_execute(execute_data)

# Validate global contracts (for service mode)
is_valid, error = validator.validate_job_status(status_data)
# job_manifest validation skipped (PLA doesn't produce public assets)
```

### HID Executor Validator (`hardware/pico-hid-executor/contract_validator.py`)
- Only validates PLA-specific contracts (action_execute, device_status)
- Does NOT validate global contracts (HID executor is not a service)

---

## Future Enhancements

### v1.1.0: Service Mode
- Add optional API endpoint for job status reporting
- Map session logs to job_status for external monitoring
- Integrate with HexForge central dashboard

### v2.0.0: Asset Publishing
- Add screenshot/video recording feature
- Use job_manifest for published session recordings
- Comply with `/assets/` public path conventions

---

## References

- [HexForge Global Contracts](https://hexforgelabs.com/docs/contracts) *(external)*
- [PLA Contracts Index](CONTRACTS_INDEX.md)
- [PLA Architecture](../docs/01_ARCHITECTURE.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
