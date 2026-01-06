#!/usr/bin/env python3
"""
Test Contract Validation

Validates that all JSON fixtures pass/fail schema validation as expected.
"""

import sys
import json
from pathlib import Path

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


def load_fixture(filename: str):
    """Load JSON fixture file."""
    fixture_path = FIXTURES_DIR / filename
    with open(fixture_path, 'r') as f:
        return json.load(f)


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
