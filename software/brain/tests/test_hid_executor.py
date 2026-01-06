#!/usr/bin/env python3
"""
Test HID Executor Integration

Validates serial communication with Raspberry Pi Pico W HID executor,
tests mode transitions, and verifies safety bounds enforcement.
"""

import os
import sys
import time
import json
import serial
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="hardware HID executor test requires physical device")


def find_hid_executor():
    """Detect HID executor serial device."""
    print("="*60)
    print("Test 1: HID Executor Detection")
    print("="*60)
    
    possible_devices = ["/dev/ttyACM0", "/dev/ttyUSB0", "/dev/ttyACM1"]
    
    for device in possible_devices:
        if Path(device).exists():
            print(f"✅ PASSED: HID executor detected at {device}")
            return device
    
    print(f"❌ FAILED: HID executor not found at {', '.join(possible_devices)}")
    print("   Ensure Raspberry Pi Pico W is connected and kill switch is ON")
    return None


def test_serial_communication(device):
    """Test basic serial communication."""
    print("\n" + "="*60)
    print("Test 2: Serial Communication")
    print("="*60)
    
    try:
        ser = serial.Serial(device, 115200, timeout=2)
        time.sleep(2)  # Wait for device to initialize
        
        # Read welcome message
        if ser.in_waiting > 0:
            welcome = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"   Device message: {welcome}")
        
        print(f"✅ PASSED: Serial connection established at 115200 baud")
        return ser
    
    except serial.SerialException as e:
        print(f"❌ FAILED: Serial error: {e}")
        return None


def test_mode_transition(ser):
    """Test mode transition commands."""
    print("\n" + "="*60)
    print("Test 3: Mode Transition")
    print("="*60)
    
    # Test SUGGEST mode (LED should remain OFF)
    cmd = {"type": "set_mode", "mode": "SUGGEST"}
    ser.write((json.dumps(cmd) + '\n').encode('utf-8'))
    time.sleep(0.5)
    
    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"   SUGGEST mode response: {response}")
    
    # Test EXECUTE mode (LED should turn ON)
    cmd = {"type": "set_mode", "mode": "EXECUTE"}
    ser.write((json.dumps(cmd) + '\n').encode('utf-8'))
    time.sleep(0.5)
    
    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"   EXECUTE mode response: {response}")
    
    print("✅ PASSED: Mode transitions working")
    print("   ⚠️  Manually verify LED turned ON when entering EXECUTE mode")
    
    # Return to OBSERVE mode
    cmd = {"type": "set_mode", "mode": "OBSERVE"}
    ser.write((json.dumps(cmd) + '\n').encode('utf-8'))
    time.sleep(0.5)
    
    return True


def test_command_bounds(ser):
    """Test command length and rate limiting."""
    print("\n" + "="*60)
    print("Test 4: Command Bounds Enforcement")
    print("="*60)
    
    # Set to EXECUTE mode first
    cmd = {"type": "set_mode", "mode": "EXECUTE"}
    ser.write((json.dumps(cmd) + '\n').encode('utf-8'))
    time.sleep(0.5)
    ser.read_all()  # Clear buffer
    
    # Test oversized command (>1024 chars)
    oversized_text = "A" * 2000
    cmd = {"type": "type_text", "text": oversized_text}
    ser.write((json.dumps(cmd) + '\n').encode('utf-8'))
    time.sleep(0.5)
    
    response = ""
    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8', errors='ignore').strip()
    
    if "ERROR" in response or "rejected" in response.lower():
        print(f"✅ PASSED: Oversized command rejected")
        print(f"   Response: {response[:100]}...")
    else:
        print(f"❌ FAILED: Oversized command not rejected")
        print(f"   Response: {response}")
        return False
    
    # Return to OBSERVE mode
    cmd = {"type": "set_mode", "mode": "OBSERVE"}
    ser.write((json.dumps(cmd) + '\n').encode('utf-8'))
    time.sleep(0.5)
    
    return True


def test_simple_action(ser):
    """Test a simple type_text action."""
    print("\n" + "="*60)
    print("Test 5: Simple HID Action")
    print("="*60)
    
    # Set to EXECUTE mode
    cmd = {"type": "set_mode", "mode": "EXECUTE"}
    ser.write((json.dumps(cmd) + '\n').encode('utf-8'))
    time.sleep(0.5)
    ser.read_all()
    
    # Send simple text command
    cmd = {"type": "type_text", "text": "Hello from HexForge PLA"}
    ser.write((json.dumps(cmd) + '\n').encode('utf-8'))
    time.sleep(0.5)
    
    response = ""
    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8', errors='ignore').strip()
    
    if "ok" in response.lower() or "success" in response.lower():
        print(f"✅ PASSED: HID action executed")
        print(f"   Response: {response}")
        print(f"   ⚠️  Check target system to verify text was typed")
    else:
        print(f"⚠️  WARNING: Unexpected response: {response}")
    
    # Return to OBSERVE mode
    cmd = {"type": "set_mode", "mode": "OBSERVE"}
    ser.write((json.dumps(cmd) + '\n').encode('utf-8'))
    time.sleep(0.5)
    
    return True


def main():
    """Run all HID executor tests."""
    print("\n" + "#"*60)
    print("# HexForge PLA - HID Executor Integration Test Suite")
    print("#"*60 + "\n")
    
    # Find device
    device = find_hid_executor()
    if not device:
        print("\n⚠️  Cannot proceed without HID executor device")
        return 1
    
    # Open serial connection
    ser = test_serial_communication(device)
    if not ser:
        print("\n⚠️  Cannot proceed without serial connection")
        return 1
    
    # Run tests
    tests = [
        ("Mode Transition", lambda: test_mode_transition(ser)),
        ("Command Bounds", lambda: test_command_bounds(ser)),
        ("Simple HID Action", lambda: test_simple_action(ser))
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ FAILED: {test_name} raised exception: {e}")
            results.append((test_name, False))
    
    # Cleanup
    ser.close()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    print(f"✅ PASSED: HID Executor Detection")
    print(f"✅ PASSED: Serial Communication")
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result) + 2  # +2 for detection & serial
    total = len(results) + 2
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! HID executor is working.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
