# HexForge PLA - Contracts Changelog

All notable changes to the PLA contract system.

---

## [v1.0.0] - 2026-01-01

### Added - Initial Contract System

**PLA-Specific Contracts (Internal Communication)**:
- ✅ `action_proposal.schema.json` - Brain → Operator action proposals
- ✅ `action_decision.schema.json` - Operator → Brain approval/rejection
- ✅ `action_execute.schema.json` - Brain → HID Executor commands
- ✅ `session_log.schema.json` - Comprehensive audit logging
- ✅ `device_status.schema.json` - HID Executor → Brain status reporting

**HexForge Global Contracts (Ecosystem Alignment)**:
- ✅ `job_status.schema.json` - Canonical job status envelope (when PLA runs as service)
- ✅ `job_manifest.schema.json` - Public asset manifest (included for ecosystem consistency, not actively used in v1)

**Validation Infrastructure**:
- ✅ Brain validator (`software/brain/src/contract_validator.py`) - Full jsonschema validation
- ✅ HID executor validator (`hardware/pico-hid-executor/contract_validator.py`) - Lightweight validation
- ✅ 15 comprehensive tests (11 PLA + 4 global) - All passing

**Documentation**:
- ✅ `CONTRACTS_INDEX.md` - Complete contract specifications
- ✅ `GLOBAL_CONTRACT_MAPPING.md` - Maps PLA contracts to global HexForge contracts
- ✅ `IMPLEMENTATION_SUMMARY.md` - Integration guide with code examples
- ✅ README and Architecture docs updated

**Safety Guarantees**:
- ✅ max_text_length: 1024 chars (enforced by schema + executor)
- ✅ min_action_delay_ms: 100ms (enforced by executor)
- ✅ mode: EXECUTE only (const in schema)
- ✅ operator_approval: Required with operator_id
- ✅ credential_warning: Mandatory boolean flag
- ✅ session_logging: checksum for tamper detection

---

## Contract Versioning Rules

Contracts follow **semantic versioning** (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes (incompatible field changes)
- **MINOR**: Backward-compatible additions (new optional fields)
- **PATCH**: Documentation/clarifications only

**Current Version**: `v1.0.0`

---

## Future Enhancements

### v1.1.0 (Planned)
- [ ] Add contract version negotiation on startup
- [ ] Implement session log checksum calculation
- [ ] Add contract violation metrics/dashboard
- [ ] Service mode: Full job_status integration for batch automation

### v2.0.0 (Planned)
- [ ] Mouse action contracts (requires calibration system)
- [ ] Encrypted payload support for sensitive data
- [ ] Contract schema evolution/migration tools
- [ ] job_manifest integration if PLA starts producing public assets
- [ ] Contract fuzzing tests for edge cases

---

## Integration Notes

### When to Use Which Contract

**PLA-Specific Contracts** (Always Use):
- `action_proposal` - Every AI-generated action suggestion
- `action_decision` - Every operator approval/rejection
- `action_execute` - Every Brain → HID command
- `session_log` - Every contract-related event
- `device_status` - Every HID → Brain status report

**Global Contracts** (Context-Dependent):
- `job_status` - When PLA runs as HexForge service (batch automation mode)
- `job_manifest` - Currently NOT used (PLA is internal tool, no public assets)

See [GLOBAL_CONTRACT_MAPPING.md](./GLOBAL_CONTRACT_MAPPING.md) for detailed mapping.

---

**Maintainer**: HexForge Team  
**Last Updated**: 2026-01-01  
**Status**: ✅ Production Ready (v1.0.0)
