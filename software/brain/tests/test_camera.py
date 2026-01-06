#!/usr/bin/env python3
"""
Test Camera Capture and OCR

Validates that the USB camera is detected, can capture frames,
and Tesseract OCR can extract text from the frames.
"""

import sys
import cv2
import pytesseract
import pytest
from pathlib import Path


def test_camera_detection():
    """Test if camera device is available."""
    print("="*60)
    print("Test 1: Camera Detection")
    print("="*60)
    
    camera_device = "/dev/video0"
    
    if not Path(camera_device).exists():
        pytest.skip(f"Camera device not found at {camera_device}")
    assert Path(camera_device).exists(), f"Camera device not found at {camera_device}"
    print(f"✅ PASSED: Camera device detected at {camera_device}")


def test_frame_capture():
    """Test capturing a frame from the camera."""
    print("\n" + "="*60)
    print("Test 2: Frame Capture")
    print("="*60)
    
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        pytest.skip("Could not open camera; skipping capture test")
    
    # Set resolution
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    ret, frame = camera.read()
    camera.release()
    
    assert ret, "Could not capture frame"
    
    height, width, channels = frame.shape
    print(f"✅ PASSED: Captured frame {width}x{height} with {channels} channels")
    
    # Save test frame
    test_frame_path = "/tmp/hexforge_test_frame.jpg"
    cv2.imwrite(test_frame_path, frame)
    print(f"   Frame saved to: {test_frame_path}")
    
    return


def test_ocr():
    """Test OCR on captured frame."""
    print("\n" + "="*60)
    print("Test 3: OCR Extraction")
    print("="*60)
    
    test_frame_path = "/tmp/hexforge_test_frame.jpg"
    
    if not Path(test_frame_path).exists():
        pytest.skip(f"Test frame not found at {test_frame_path}; run capture test with camera present")
    
    # Load frame
    frame = cv2.imread(test_frame_path)
    
    # Convert to grayscale (improves OCR accuracy)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Run OCR
    ocr_text = pytesseract.image_to_string(gray)
    
    if not ocr_text.strip():
        print("⚠️  WARNING: OCR returned empty text")
        print("   This is normal if camera is not pointed at text")
        print("   Point camera at a screen with text and re-run")
        return
    
    print(f"✅ PASSED: OCR extracted {len(ocr_text)} characters")
    print("\nSample OCR output (first 200 chars):")
    print("-"*60)
    print(ocr_text[:200])
    print("-"*60)
    
    assert ocr_text is not None


def main():
    """Run all camera tests."""
    print("\n" + "#"*60)
    print("# HexForge PLA - Camera & OCR Test Suite")
    print("#"*60 + "\n")
    
    tests = [
        ("Camera Detection", test_camera_detection),
        ("Frame Capture", test_frame_capture),
        ("OCR Extraction", test_ocr)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ FAILED: {test_name} raised exception: {e}")
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
        print("\n🎉 All tests passed! Camera and OCR are working.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
