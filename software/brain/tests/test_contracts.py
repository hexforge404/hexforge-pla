#!/usr/bin/env python3
"""
Test Contract Validation

Validates that all JSON fixtures pass/fail schema validation as expected.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, FormatChecker

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contract_validator import (
    validate_proposal,
    validate_decision,
    validate_execute,
    validate_session_log,
    validate_device_status,
    validate_job_status
)


FIXTURES_DIR = Path(__file__).parent / 'fixtures'
SCHEMAS_DIR = Path(__file__).parent.parent.parent.parent / 'contracts' / 'schemas'


def load_fixture(filename: str):
    """Load JSON fixture file."""
    fixture_path = FIXTURES_DIR / filename
    with open(fixture_path, 'r') as f:
        return json.load(f)


def load_schema(filename: str):
    """Load a JSON contract schema."""
    with open(SCHEMAS_DIR / filename, 'r') as f:
        return json.load(f)


def strict_validator(filename: str) -> Draft7Validator:
    """Build a validator that enforces JSON Schema formats explicitly."""
    schema = load_schema(filename)
    Draft7Validator.check_schema(schema)
    checker = FormatChecker()

    def canonical_utc_datetime(value):
        if not isinstance(value, str):
            return True  # JSON Schema type validation reports non-strings.
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        return True

    checker.checkers["date-time"] = (canonical_utc_datetime, (ValueError,))
    return Draft7Validator(schema, format_checker=checker)


def test_valid_proposal_type_text():
    """Test valid TYPE_TEXT proposal."""
    print("\n" + "="*60)
    print("Test: Valid Proposal (TYPE_TEXT)")
    print("="*60)
    
    data = load_fixture('valid_proposal_type_text.json')
    is_valid, error = validate_proposal(data)
    
    print("✅ PASSED: Proposal validated successfully")
    assert is_valid, error


def test_valid_proposal_key_combo():
    """Test valid KEY_COMBO proposal."""
    print("\n" + "="*60)
    print("Test: Valid Proposal (KEY_COMBO)")
    print("="*60)
    
    data = load_fixture('valid_proposal_key_combo.json')
    is_valid, error = validate_proposal(data)
    
    print("✅ PASSED: Key combo proposal validated successfully")
    assert is_valid, error


def test_valid_proposal_with_credential_warning():
    """Test proposal with credential warning."""
    print("\n" + "="*60)
    print("Test: Valid Proposal with Credential Warning")
    print("="*60)
    
    data = load_fixture('valid_proposal_with_credential_warning.json')
    is_valid, error = validate_proposal(data)
    
    print("✅ PASSED: Proposal with credential warning validated")
    print("   ⚠️  Credential warning flag: TRUE")
    assert is_valid and data['credential_warning'], error


def test_valid_decision_approved():
    """Test valid APPROVED decision."""
    print("\n" + "="*60)
    print("Test: Valid Decision (APPROVED)")
    print("="*60)
    
    data = load_fixture('valid_decision_approved.json')
    is_valid, error = validate_decision(data)
    
    print("✅ PASSED: Approved decision validated successfully")
    assert is_valid, error


def test_valid_decision_rejected():
    """Test valid REJECTED decision with reason."""
    print("\n" + "="*60)
    print("Test: Valid Decision (REJECTED)")
    print("="*60)
    
    data = load_fixture('valid_decision_rejected.json')
    is_valid, error = validate_decision(data)
    
    print("✅ PASSED: Rejected decision validated with reason")
    print(f"   Reason: {data['override_reason']}")
    assert is_valid and 'override_reason' in data, error


def test_valid_execute_type_text():
    """Test valid execute command."""
    print("\n" + "="*60)
    print("Test: Valid Execute Command (TYPE_TEXT)")
    print("="*60)
    
    data = load_fixture('valid_execute_type_text.json')
    is_valid, error = validate_execute(data)
    
    print("✅ PASSED: Execute command validated successfully")
    print(f"   Mode: {data['mode']} (correct)")
    assert is_valid and data['mode'] == 'EXECUTE', error


def test_invalid_execute_wrong_mode():
    """Test execute command with wrong mode (should fail)."""
    print("\n" + "="*60)
    print("Test: Invalid Execute Command (Wrong Mode)")
    print("="*60)
    
    data = load_fixture('invalid_execute_wrong_mode.json')
    is_valid, error = validate_execute(data)
    
    print("✅ PASSED: Invalid mode correctly rejected")
    print(f"   Error: {error}")
    assert not is_valid, "Should have rejected mode != EXECUTE"


def test_valid_session_log():
    """Test valid session log entry."""
    print("\n" + "="*60)
    print("Test: Valid Session Log Entry")
    print("="*60)
    
    data = load_fixture('valid_session_log_proposal.json')
    is_valid, error = validate_session_log(data)
    
    print("✅ PASSED: Session log entry validated successfully")
    print(f"   Event type: {data['event_type']}")
    print(f"   Checksum: {data['checksum'][:16]}...")
    assert is_valid, error


def test_valid_device_status():
    """Test valid device status report."""
    print("\n" + "="*60)
    print("Test: Valid Device Status Report")
    print("="*60)
    
    data = load_fixture('valid_device_status.json')
    is_valid, error = validate_device_status(data)
    
    print("✅ PASSED: Device status validated successfully")
    print(f"   Device: {data['device_id']}")
    print(f"   Mode: {data['mode']}")
    print(f"   LED: {'ON' if data['led_state'] else 'OFF'}")
    print(f"   Kill switch: {data['kill_switch_state']}")
    assert is_valid, error


@pytest.mark.parametrize("kill_state", ["ARMED", "DISABLED", "UNKNOWN"])
def test_device_status_preserves_kill_switch_enum(kill_state):
    data = load_fixture('valid_device_status.json')
    data['kill_switch_state'] = kill_state
    strict_validator('device_status.schema.json').validate(data)


@pytest.mark.parametrize("missing", ["timestamp", "boot_id", "sync_id", "status_sequence"])
def test_device_status_rejects_missing_provenance(missing):
    data = load_fixture('valid_device_status.json')
    del data[missing]
    assert not strict_validator('device_status.schema.json').is_valid(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("timestamp", "2026-01-01T10:30:00Z"),
        ("timestamp", "2026-01-01T10:30:00.000+00:00"),
        ("timestamp", "2026-13-40T25:61:61.000Z"),
        ("timestamp", "not-a-timestamp"),
        ("timestamp", None),
        ("boot_id", "ABCDEF0123456789ABCDEF0123456789"),
        ("boot_id", "0123456789abcdef"),
        ("boot_id", True),
        ("sync_id", "xyz"),
        ("sync_id", 1),
        ("status_sequence", True),
        ("status_sequence", "0"),
        ("status_sequence", 1.5),
        ("status_sequence", -1),
        ("status_sequence", 9223372036854775808),
    ],
)
def test_device_status_rejects_noncanonical_provenance(field, value):
    data = load_fixture('valid_device_status.json')
    data[field] = value
    assert not strict_validator('device_status.schema.json').is_valid(data)


def test_legacy_device_status_is_not_authoritative():
    data = load_fixture('valid_device_status.json')
    for field in ("boot_id", "sync_id", "status_sequence"):
        del data[field]
    assert not strict_validator('device_status.schema.json').is_valid(data)


@pytest.mark.parametrize("kill_state", ["armed", " ARMED", "ARMED ", True, 1, None])
def test_device_status_rejects_noncanonical_kill_state(kill_state):
    data = load_fixture('valid_device_status.json')
    data['kill_switch_state'] = kill_state
    assert not strict_validator('device_status.schema.json').is_valid(data)


def test_device_status_rejects_extra_fields():
    data = load_fixture('valid_device_status.json')
    data['physical_ok'] = True
    assert not strict_validator('device_status.schema.json').is_valid(data)


def test_valid_device_time_sync():
    data = load_fixture('valid_device_time_sync.json')
    strict_validator('device_time_sync.schema.json').validate(data)


@pytest.mark.parametrize("missing", ["type", "sync_id", "utc_anchor"])
def test_device_time_sync_rejects_missing_fields(missing):
    data = load_fixture('valid_device_time_sync.json')
    del data[missing]
    assert not strict_validator('device_time_sync.schema.json').is_valid(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("type", "sync"),
        ("type", True),
        ("sync_id", "FEDCBA9876543210FEDCBA9876543210"),
        ("sync_id", "short"),
        ("sync_id", None),
        ("utc_anchor", "2026-01-01T10:30:00Z"),
        ("utc_anchor", "2026-01-01T10:30:00.000+00:00"),
        ("utc_anchor", "2026-13-40T25:61:61.000Z"),
        ("utc_anchor", "not-a-timestamp"),
        ("utc_anchor", 0),
    ],
)
def test_device_time_sync_rejects_noncanonical_fields(field, value):
    data = load_fixture('valid_device_time_sync.json')
    data[field] = value
    assert not strict_validator('device_time_sync.schema.json').is_valid(data)


def test_device_time_sync_rejects_extra_fields():
    data = load_fixture('valid_device_time_sync.json')
    data['timestamp'] = data['utc_anchor']
    assert not strict_validator('device_time_sync.schema.json').is_valid(data)


def test_invalid_proposal_missing_field():
    """Test proposal with missing required field."""
    print("\n" + "="*60)
    print("Test: Invalid Proposal (Missing Required Field)")
    print("="*60)
    
    # Load valid and remove required field
    data = load_fixture('valid_proposal_type_text.json')
    del data['rationale']  # Remove required field
    
    is_valid, error = validate_proposal(data)
    
    print("✅ PASSED: Missing 'rationale' correctly rejected")
    print(f"   Error: {error}")
    assert not is_valid and 'rationale' in str(error), "Should have rejected missing 'rationale'"


def test_invalid_proposal_text_too_long():
    """Test proposal with text exceeding max length."""
    print("\n" + "="*60)
    print("Test: Invalid Proposal (Text Too Long)")
    print("="*60)
    
    # Load valid and exceed bounds
    data = load_fixture('valid_proposal_type_text.json')
    data['payload']['text'] = 'A' * 2000  # Exceeds 1024 char limit
    
    is_valid, error = validate_proposal(data)
    
    print("✅ PASSED: Oversized text correctly rejected")
    print(f"   Error: {error}")
    assert not is_valid, "Should have rejected text > 1024 chars"


def test_valid_job_status_running():
    """Test valid job_status (running state)."""
    print("\n" + "="*60)
    print("Test: Valid Job Status (Running)")
    print("="*60)
    
    data = load_fixture('valid_job_status_running.json')
    is_valid, error = validate_job_status(data)
    
    print("✅ PASSED: Job status (running) validated successfully")
    assert is_valid, error


def test_valid_job_status_complete():
    """Test valid job_status (complete state)."""
    print("\n" + "="*60)
    print("Test: Valid Job Status (Complete)")
    print("="*60)
    
    data = load_fixture('valid_job_status_complete.json')
    is_valid, error = validate_job_status(data)
    
    print("✅ PASSED: Job status (complete) validated successfully")
    assert is_valid, error


def test_valid_job_status_failed():
    """Test valid job_status (failed state)."""
    print("\n" + "="*60)
    print("Test: Valid Job Status (Failed)")
    print("="*60)
    
    data = load_fixture('valid_job_status_failed.json')
    is_valid, error = validate_job_status(data)
    
    print("✅ PASSED: Job status (failed) validated successfully")
    assert is_valid, error


def test_invalid_job_status_wrong_enum():
    """Test job_status with invalid status enum value."""
    print("\n" + "="*60)
    print("Test: Invalid Job Status (Wrong Enum)")
    print("="*60)
    
    data = load_fixture('invalid_job_status_wrong_enum.json')
    is_valid, error = validate_job_status(data)
    
    print("✅ PASSED: Invalid status enum correctly rejected")
    print(f"   Error: {error}")
    assert not is_valid, "Should have rejected invalid status enum"


def main():
    """Run all contract validation tests."""
    print("\n" + "#"*60)
    print("# HexForge PLA - Contract Validation Test Suite")
    print("#"*60)
    
    tests = [
        ("Valid Proposal (TYPE_TEXT)", test_valid_proposal_type_text),
        ("Valid Proposal (KEY_COMBO)", test_valid_proposal_key_combo),
        ("Valid Proposal (Credential Warning)", test_valid_proposal_with_credential_warning),
        ("Valid Decision (APPROVED)", test_valid_decision_approved),
        ("Valid Decision (REJECTED)", test_valid_decision_rejected),
        ("Valid Execute Command", test_valid_execute_type_text),
        ("Invalid Execute (Wrong Mode)", test_invalid_execute_wrong_mode),
        ("Valid Session Log", test_valid_session_log),
        ("Valid Device Status", test_valid_device_status),
        ("Invalid Proposal (Missing Field)", test_invalid_proposal_missing_field),
        ("Invalid Proposal (Text Too Long)", test_invalid_proposal_text_too_long),
        ("Valid Job Status (Running)", test_valid_job_status_running),
        ("Valid Job Status (Complete)", test_valid_job_status_complete),
        ("Valid Job Status (Failed)", test_valid_job_status_failed),
        ("Invalid Job Status (Wrong Enum)", test_invalid_job_status_wrong_enum),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ FAILED: {test_name} raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All contract validation tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
