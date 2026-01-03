# Hardware Bring-Up Plan — HexForge PLA

**Purpose**: Step-by-step guide to assemble, test, and validate hardware components from bare parts to working system.

**Approach**: Bottom-up integration with safety validation at each stage.

---

## Overview

### Bring-Up Phases

1. **Component Validation** - Test individual parts
2. **HID Executor Assembly** - Build and test constrained execution zone
3. **Brain Setup** - Configure trusted computing environment
4. **Camera Integration** - Add vision capabilities
5. **System Integration** - Connect all components
6. **Safety Validation** - Verify all safety mechanisms
7. **End-to-End Testing** - Full workflow validation

### Prerequisites

- All components from [Hardware BOM](04_HARDWARE_BOM.md) acquired
- Basic soldering tools (if custom wiring needed)
- Multimeter for power testing
- Lab bench with good lighting
- Target test machine (VM or dedicated laptop)

---

## Phase 1: Component Validation

**Goal**: Verify each component works independently before integration.

### 1.1. Kill Switch Test

**Components**: SPST toggle switch, multimeter

**Procedure**:
```
1. Set multimeter to continuity mode (Ω)
2. Connect probes to switch terminals
3. Toggle switch to ON position
   Expected: Continuity beep
4. Toggle switch to OFF position
   Expected: No continuity (open circuit)
5. Repeat 10 times
   Expected: Consistent behavior
```

**Pass Criteria**: ✅ Switch opens/closes circuit reliably

**Failure Action**: Replace switch (safety-critical component)

---

### 1.2. LED Indicator Test

**Components**: Red 5mm LED, 330Ω resistor, 3.3V power source

**Procedure**:
```
1. Connect LED + resistor in series
2. Apply 3.3V across the circuit
   Expected: LED illuminates (red)
3. Reverse polarity
   Expected: LED does not illuminate
4. Measure voltage drop across LED
   Expected: ~1.8-2.2V
5. Measure current through circuit
   Expected: ~6-8mA
```

**Pass Criteria**: ✅ LED illuminates at correct voltage, current within spec

**Failure Action**: Check resistor value (330Ω for 3.3V), replace LED if damaged

---

### 1.3. Raspberry Pi Pico W Test

**Components**: Pico W, USB cable, computer

**Procedure**:
```
1. Connect Pico W to computer via USB
2. Hold BOOTSEL button while plugging in
   Expected: Pico appears as USB mass storage (RPI-RP2)
3. Download CircuitPython 8.x UF2 from circuitpython.org
4. Copy UF2 file to RPI-RP2 drive
   Expected: Pico reboots, appears as CIRCUITPY drive
5. Create test file: lib/test.py
   ```python
   print("Hello from Pico W")
   ```
6. Check serial output (115200 baud)
   Expected: "Hello from Pico W" appears
```

**Pass Criteria**: ✅ CircuitPython boots, serial communication works

**Failure Action**: Re-flash CircuitPython, check USB cable quality

---

### 1.4. USB Webcam Test

**Components**: Webcam, USB cable, computer with Linux

**Procedure**:
```bash
# 1. Connect webcam to computer
# 2. List video devices
ls -l /dev/video*
# Expected: /dev/video0 appears

# 3. Check device capabilities
v4l2-ctl --device=/dev/video0 --all
# Expected: Lists supported resolutions, formats

# 4. Capture test frame
ffmpeg -f v4l2 -i /dev/video0 -frames 1 test_frame.jpg
# Expected: test_frame.jpg created

# 5. Verify resolution
file test_frame.jpg
# Expected: 1920x1080 (if C920/C922)
```

**Pass Criteria**: ✅ Camera detected, captures frames at expected resolution

**Failure Action**: Check USB 3.0 connection, try different USB port

---

### 1.5. Brain Platform Test

**Option A: Raspberry Pi 4**
```bash
# 1. Flash Raspberry Pi OS to microSD
sudo dd if=raspios.img of=/dev/sdX bs=4M status=progress

# 2. Boot RPi4 with monitor/keyboard
# 3. Complete initial setup
# 4. Update system
sudo apt update && sudo apt upgrade -y

# 5. Verify Python version
python3 --version
# Expected: Python 3.11+ (or install from source)

# 6. Test camera interface
vcgencmd get_camera
# Expected: supported=1 detected=1 (if RPi camera used)
```

**Option B: Proxmox VM**
```bash
# 1. Create VM in Proxmox UI
# - OS: Ubuntu Server 22.04 LTS
# - CPU: 2 cores
# - RAM: 4GB
# - Disk: 20GB
# - Network: Bridged

# 2. Install OS
# 3. Configure SSH access
# 4. Update system
sudo apt update && sudo apt upgrade -y

# 5. Verify USB passthrough (if needed for camera)
lsusb
# Expected: Lists USB devices visible to VM
```

**Pass Criteria**: ✅ Brain platform boots, network accessible, Python available

**Failure Action**: Check SD card (RPi4) or VM config (Proxmox)

---

## Phase 2: HID Executor Assembly

**Goal**: Build functional HID executor with safety mechanisms.

### 2.1. Install CircuitPython Libraries

**Prerequisites**: Pico W with CircuitPython installed

**Procedure**:
```
1. Download Adafruit CircuitPython Bundle 8.x
   URL: https://circuitpython.org/libraries

2. Extract bundle to computer

3. Copy required libraries to Pico W:
   CIRCUITPY/lib/
   ├── adafruit_hid/
   │   ├── __init__.py
   │   ├── keyboard.py
   │   ├── keycode.py
   │   └── mouse.py

4. Verify installation:
   - Check CIRCUITPY/lib/ directory
   - Expected: adafruit_hid folder present
```

**Pass Criteria**: ✅ Libraries copied successfully

---

### 2.2. Wire LED Indicator

**Components**: Pico W, LED, 330Ω resistor, jumper wires

**Circuit**:
```
Pico W GPIO 2 ──┬── 330Ω Resistor ──┬── LED Anode (+)
                │                    │
                │                    └── LED Cathode (-)
                │                         │
Pico W GND ─────┴─────────────────────────┘
```

**Procedure**:
```
1. Power off Pico W
2. Connect 330Ω resistor to GPIO 2
3. Connect LED anode to resistor
4. Connect LED cathode to GND
5. Use breadboard for temporary connections
6. Power on Pico W
7. Test with Python:
   ```python
   import board
   import digitalio
   
   led = digitalio.DigitalInOut(board.GP2)
   led.direction = digitalio.Direction.OUTPUT
   led.value = True  # Should light up
   ```
```

**Pass Criteria**: ✅ LED illuminates when GPIO 2 is high

**Failure Action**: Check polarity (LED has flat side = cathode), verify resistor value

---

### 2.3. Wire Kill Switch

**Components**: Pico W, kill switch, USB cable, wire cutters

**Circuit**:
```
USB Power (+5V) ──┬── Kill Switch ──┬── Pico W VBUS
                  │                 │
USB GND ──────────┴─────────────────┴── Pico W GND
```

**Procedure**:
```
1. Cut USB cable (use spare, not main cable)
2. Strip wires to expose conductors
3. Identify VBUS (red) and GND (black)
4. Connect VBUS through kill switch
5. Connect GND directly (no switch)
6. Solder connections (or use screw terminals)
7. Insulate with heat shrink tubing
8. Test:
   - Switch ON: Pico W powers up
   - Switch OFF: Pico W has no power
```

**⚠️ SAFETY WARNING**: 
- Kill switch MUST be inline with VBUS (power)
- Do NOT use GPIO for kill switch (can be bypassed in software)
- Test thoroughly before proceeding

**Pass Criteria**: ✅ Kill switch completely removes power from Pico W

**Failure Action**: Re-wire if switch is on wrong conductor (must be VBUS)

---

### 2.4. Flash HID Executor Firmware

**Prerequisites**: Pico W with CircuitPython, libraries installed

**Procedure**:
```bash
# 1. Copy firmware files to Pico W
cp hardware/pico-hid-executor/main.py /media/CIRCUITPY/
cp hardware/pico-hid-executor/contract_validator.py /media/CIRCUITPY/

# 2. Verify files copied
ls /media/CIRCUITPY/
# Expected: main.py, contract_validator.py, lib/

# 3. Pico W auto-reboots, check serial output
screen /dev/ttyACM0 115200
# Expected: Firmware initialization messages

# 4. Test serial communication
echo '{"mode":"OBSERVE"}' > /dev/ttyACM0
# Expected: Pico responds with status message
```

**Pass Criteria**: ✅ Firmware boots, responds to serial commands

**Failure Action**: Check serial connection (115200 baud), verify file syntax

---

### 2.5. HID Executor Functional Test

**Prerequisites**: Firmware flashed, target test machine available

**Test Script**:
```python
#!/usr/bin/env python3
import serial
import json
import time

# Connect to Pico W
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)
time.sleep(2)  # Wait for initialization

# Test 1: Set mode to EXECUTE
command = {"mode": "EXECUTE"}
ser.write((json.dumps(command) + '\n').encode())
response = ser.readline().decode().strip()
print(f"Mode response: {response}")

# Test 2: Type text (on target machine)
command = {
    "command_id": "test-001",
    "timestamp": "2026-01-01T10:00:00Z",
    "mode": "EXECUTE",
    "action_type": "TYPE_TEXT",
    "payload": {"text": "Hello World"},
    "operator_approval": {"operator_id": "test"},
    "safety_bounds": {"max_text_length": 1024, "min_action_delay_ms": 100}
}
ser.write((json.dumps(command) + '\n').encode())
response = ser.readline().decode().strip()
print(f"Execute response: {response}")

# Test 3: Check LED state
# Expected: LED is ON when mode=EXECUTE

# Test 4: Toggle kill switch
# Expected: Pico W loses power, LED turns OFF

ser.close()
```

**Pass Criteria**:
- ✅ Mode changes accepted
- ✅ Text typed on target machine
- ✅ LED indicates mode correctly
- ✅ Kill switch removes power

**Failure Action**: Debug serial communication, check HID connection to target

---

## Phase 3: Brain Setup

**Goal**: Configure trusted computing environment with dependencies.

### 3.1. Brain Platform Configuration

**For Raspberry Pi 4**:
```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv git

# 2. Install camera tools
sudo apt install -y v4l-utils tesseract-ocr

# 3. Install Ollama (if RAM permits)
curl -fsSL https://ollama.com/install.sh | sh

# 4. Clone repository
git clone <repo-url> /home/pi/hexforge-pla
cd /home/pi/hexforge-pla
```

**For Proxmox VM**:
```bash
# 1. SSH into VM
ssh user@brain-vm-ip

# 2. Install dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv git
sudo apt install -y v4l-utils tesseract-ocr

# 3. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 4. Clone repository
git clone <repo-url> /opt/hexforge-pla
cd /opt/hexforge-pla
```

**Pass Criteria**: ✅ All dependencies installed, repository cloned

---

### 3.2. Python Environment Setup

```bash
# 1. Create virtual environment
cd software/brain
python3 -m venv venv

# 2. Activate environment
source venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install requirements
pip install -r requirements.txt

# 5. Verify installations
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
python3 -c "import pytesseract; print('Tesseract OK')"
python3 -c "import jsonschema; print('jsonschema OK')"
python3 -c "import serial; print('pyserial OK')"
```

**Pass Criteria**: ✅ All Python packages import successfully

**Failure Action**: Check pip logs, install system dependencies if needed

---

### 3.3. Contract Validation Test

```bash
# Run contract tests
cd /opt/hexforge-pla  # or /home/pi/hexforge-pla
python3 software/brain/tests/test_contracts.py

# Expected output:
# ============================================================
# # HexForge PLA - Contract Validation Test Suite
# ============================================================
# 
# Test: Valid Proposal (TYPE_TEXT)
# ✅ PASSED
# 
# ... (all tests)
# 
# Total: 15/15 tests passed
# 🎉 All contract validation tests passed!
```

**Pass Criteria**: ✅ 15/15 tests pass

**Failure Action**: Check Python version (3.11+), verify jsonschema installed

---

## Phase 4: Camera Integration

**Goal**: Add vision capabilities and test capture pipeline.

### 4.1. Camera Physical Setup

**Procedure**:
```
1. Connect webcam to Brain via USB 3.0
   - RPi4: Use blue USB 3.0 ports
   - VM: Ensure USB passthrough configured

2. Position camera to view target screen
   - Use adjustable arm or tripod
   - Minimize glare/reflections
   - Center target screen in frame

3. Secure camera position
   - Tighten mount/tripod
   - Route cable to avoid obstruction
```

**Pass Criteria**: ✅ Camera physically positioned and connected

---

### 4.2. Camera Detection Test

```bash
# 1. List video devices
ls -l /dev/video*
# Expected: /dev/video0 (or video1 if built-in camera present)

# 2. Check device info
v4l2-ctl --device=/dev/video0 --all
# Expected: Device capabilities listed

# 3. List supported formats
v4l2-ctl --device=/dev/video0 --list-formats-ext
# Expected: 1920x1080 @ 30fps available

# 4. Capture test frame
ffmpeg -f v4l2 -i /dev/video0 -frames 1 -s 1920x1080 test_capture.jpg
# Expected: test_capture.jpg created

# 5. View captured frame
# Expected: Clear image of target screen
```

**Pass Criteria**: ✅ Camera detected, captures 1080p frames

**Failure Action**: Check USB connection, verify drivers loaded (lsusb)

---

### 4.3. OCR Test

```bash
# 1. Prepare test image with known text
# (Use test_capture.jpg from previous step, or create simple text image)

# 2. Run Tesseract OCR
tesseract test_capture.jpg output_text

# 3. Check extracted text
cat output_text.txt
# Expected: Text visible in image is extracted

# 4. Test with Python
python3 << 'EOF'
import cv2
import pytesseract

# Load image
img = cv2.imread('test_capture.jpg')

# Extract text
text = pytesseract.image_to_string(img)
print("Extracted text:")
print(text)
EOF
```

**Pass Criteria**: ✅ Tesseract extracts text from captured frames

**Failure Action**: Install language data (sudo apt install tesseract-ocr-eng)

---

### 4.4. Camera Module Integration Test

```bash
# Run camera integration test
python3 software/brain/tests/test_camera.py

# Expected output:
# ============================================================
# Test 1: Camera Detection
# ============================================================
# ✅ PASSED: Camera device detected at /dev/video0
# 
# ============================================================
# Test 2: Frame Capture
# ============================================================
# ✅ PASSED: Frame captured (1920x1080)
# 
# ============================================================
# Test 3: OCR Extraction
# ============================================================
# ✅ PASSED: Text extracted from frame
```

**Pass Criteria**: ✅ All camera tests pass

**Failure Action**: Check camera connection, verify OpenCV/Tesseract installed

---

## Phase 5: System Integration

**Goal**: Connect all components and test end-to-end communication.

### 5.1. Physical Assembly

**Layout**:
```
┌─────────────────────────────────────────┐
│  Lab Bench or Portable Case             │
│                                         │
│  [Brain] ──USB─► [Camera]              │
│     │                  │                │
│     │                  └─► (aimed at    │
│     │                       target)     │
│     │                                   │
│  [USB Serial]                           │
│     │                                   │
│  [HID Executor] ──USB HID─► [Target]   │
│     ▲                                   │
│     │                                   │
│  [Kill Switch] ◄─── Operator           │
│     │                                   │
│  [LED Indicator] (visible)              │
│                                         │
└─────────────────────────────────────────┘
```

**Checklist**:
- [ ] Brain powered and accessible (SSH or local)
- [ ] Camera connected to Brain USB 3.0
- [ ] HID Executor connected to Brain USB 2.0 (serial)
- [ ] HID Executor connected to Target (USB HID)
- [ ] Kill switch accessible to operator
- [ ] LED indicator visible to operator
- [ ] All cables secured and managed

---

### 5.2. Serial Communication Test

```bash
# On Brain, test HID Executor connection
python3 software/brain/tests/test_hid_executor.py

# Expected output:
# ============================================================
# Test 1: HID Executor Detection
# ============================================================
# ✅ PASSED: HID executor detected at /dev/ttyACM0
# 
# ============================================================
# Test 2: Serial Communication
# ============================================================
# ✅ PASSED: Serial connection established at 115200 baud
# 
# ============================================================
# Test 3: Mode Transitions
# ============================================================
# ✅ PASSED: Mode changed to EXECUTE
# 
# ============================================================
# Test 4: Type Text Command
# ============================================================
# ✅ PASSED: Text typed on target machine
```

**Pass Criteria**: ✅ All HID communication tests pass

**Failure Action**: Check serial device (/dev/ttyACM0), verify firmware running

---

### 5.3. End-to-End Functional Test

**Manual Test Procedure**:

```
1. Start Brain main loop (scaffolding)
   cd /opt/hexforge-pla/software/brain
   source venv/bin/activate
   python3 src/main.py
   # Expected: Logs initialization messages

2. Verify mode starts in OBSERVE
   # Expected: LED is OFF (HID disabled)

3. (Future: Web UI will allow mode changes)
   # For now, manually send commands via serial

4. Test kill switch safety
   a. Set mode to EXECUTE (LED should turn ON)
   b. Queue action (type text)
   c. Toggle kill switch to OFF during execution
   d. Expected: Pico W loses power, action stops
   e. Toggle kill switch to ON
   f. Expected: Pico W reboots, mode resets to OBSERVE

5. Test camera capture
   # Open target screen (e.g., text editor)
   # Brain should capture frames (logged in debug mode)

6. Verify session logging
   # Check logs directory for session log files
   # Expected: All events logged with timestamps
```

**Pass Criteria**:
- ✅ System boots in OBSERVE mode
- ✅ Camera captures frames
- ✅ HID executor responds to commands
- ✅ Kill switch interrupts execution
- ✅ LED indicates mode correctly

**Failure Action**: Debug each component individually, check logs

---

## Phase 6: Safety Validation

**Goal**: Verify all safety mechanisms function correctly.

### 6.1. Kill Switch Validation

**Test: SAFE-001 - Kill switch disables HID power**
```
1. Set mode to EXECUTE
2. Verify LED is ON
3. Toggle kill switch to OFF
4. Expected: Pico W loses power immediately
5. Expected: LED turns OFF
6. Verify with multimeter: No voltage at Pico W VBUS
7. Toggle kill switch to ON
8. Expected: Pico W boots (may take 2-3 seconds)
```

**Pass Criteria**: ✅ Kill switch completely removes power

---

**Test: SAFE-002 - Kill switch stops action mid-execution**
```
1. Set mode to EXECUTE
2. Queue action: Type long text (100+ characters)
3. During execution, toggle kill switch to OFF
4. Expected: Typing stops immediately
5. Expected: Target receives partial text only
6. Verify Pico W has no power
```

**Pass Criteria**: ✅ Action halts immediately when power removed

---

**Test: SAFE-003 - Kill switch prevents reboot bypass**
```
1. Toggle kill switch to OFF
2. Attempt to flash new firmware
3. Expected: Pico W cannot enter bootloader (no power)
4. Hold BOOTSEL button and toggle switch to ON
5. Expected: Pico W enters bootloader
6. Release BOOTSEL, toggle switch OFF
7. Expected: Pico W remains powered off
```

**Pass Criteria**: ✅ Kill switch cannot be bypassed in hardware or firmware

---

### 6.2. Command Bounds Validation

**Test: BOUND-001 - Reject text > 1024 chars**
```bash
# Create oversized text command
python3 << 'EOF'
import serial
import json

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)

command = {
    "command_id": "test-oversized",
    "timestamp": "2026-01-01T10:00:00Z",
    "mode": "EXECUTE",
    "action_type": "TYPE_TEXT",
    "payload": {"text": "A" * 2000},  # 2000 chars (exceeds 1024)
    "operator_approval": {"operator_id": "test"},
    "safety_bounds": {"max_text_length": 1024, "min_action_delay_ms": 100}
}

ser.write((json.dumps(command) + '\n').encode())
response = ser.readline().decode().strip()
print(response)
# Expected: {"status": "error", "message": "text length exceeds MAX_TEXT_LENGTH"}

ser.close()
EOF
```

**Pass Criteria**: ✅ Oversized commands rejected by HID executor

---

**Test: BOUND-002 - Rate limiting enforced**
```bash
# Send rapid commands
python3 << 'EOF'
import serial
import json
import time

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)

# Send 3 commands rapidly (< 100ms apart)
for i in range(3):
    command = {
        "command_id": f"test-rapid-{i}",
        "timestamp": "2026-01-01T10:00:00Z",
        "mode": "EXECUTE",
        "action_type": "TYPE_TEXT",
        "payload": {"text": "Fast"},
        "operator_approval": {"operator_id": "test"},
        "safety_bounds": {"max_text_length": 1024, "min_action_delay_ms": 100}
    }
    ser.write((json.dumps(command) + '\n').encode())
    print(f"Sent command {i}")
    time.sleep(0.05)  # 50ms delay (less than MIN_ACTION_DELAY_MS)

# Expected: Commands queued, but executed with min 100ms delay
ser.close()
EOF
```

**Pass Criteria**: ✅ HID executor enforces 100ms minimum delay between actions

---

### 6.3. Mode Validation

**Test: MODE-001 - HID disabled in OBSERVE mode**
```bash
python3 << 'EOF'
import serial
import json

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)

# Set mode to OBSERVE
mode_cmd = {"mode": "OBSERVE"}
ser.write((json.dumps(mode_cmd) + '\n').encode())
print(ser.readline().decode().strip())

# Attempt to execute action
action_cmd = {
    "command_id": "test-blocked",
    "timestamp": "2026-01-01T10:00:00Z",
    "mode": "EXECUTE",
    "action_type": "TYPE_TEXT",
    "payload": {"text": "Blocked"},
    "operator_approval": {"operator_id": "test"},
    "safety_bounds": {"max_text_length": 1024, "min_action_delay_ms": 100}
}
ser.write((json.dumps(action_cmd) + '\n').encode())
response = ser.readline().decode().strip()
print(response)
# Expected: {"status": "error", "message": "HID disabled in OBSERVE mode"}

# Verify LED is OFF
# Expected: LED not illuminated

ser.close()
EOF
```

**Pass Criteria**: ✅ HID actions rejected when mode != EXECUTE

---

**Test: MODE-002 - LED indicates EXECUTE mode**
```bash
# Test LED behavior across mode transitions
python3 << 'EOF'
import serial
import json
import time

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)

modes = ["OBSERVE", "SUGGEST", "EXECUTE", "OBSERVE"]

for mode in modes:
    cmd = {"mode": mode}
    ser.write((json.dumps(cmd) + '\n').encode())
    response = ser.readline().decode().strip()
    print(f"Mode: {mode}, Response: {response}")
    
    # Manual verification
    input(f"Verify LED state for {mode}. Press Enter to continue...")
    # Expected:
    # - OBSERVE: LED OFF
    # - SUGGEST: LED OFF
    # - EXECUTE: LED ON
    # - OBSERVE: LED OFF

ser.close()
EOF
```

**Pass Criteria**: ✅ LED ON only when mode=EXECUTE, OFF otherwise

---

## Phase 7: End-to-End Testing

**Goal**: Validate complete workflows with all components integrated.

### 7.1. Observe Mode Workflow

```
1. Start Brain main loop
2. Verify mode = OBSERVE
3. Open test application on target (e.g., text editor)
4. Camera captures screen
5. (Future) AI summarizes screen state
6. Verify: No HID actions possible
7. Verify: LED is OFF
```

**Pass Criteria**: ✅ System observes without executing actions

---

### 7.2. Suggest Mode Workflow (Future)

```
1. Transition to SUGGEST mode
2. AI analyzes screen
3. AI proposes action (e.g., "Type username")
4. Proposal displayed in web UI
5. Operator reviews proposal
6. Operator DENIES action
7. Verify: No HID execution occurs
8. Verify: Denial logged in session log
```

**Pass Criteria**: ✅ Proposals generated but not executed without approval

---

### 7.3. Execute Mode Workflow (Future)

```
1. Transition to EXECUTE mode
2. Verify LED turns ON
3. AI proposes action
4. Operator APPROVES action
5. Brain sends command to HID executor
6. HID executor validates contract
7. HID executor types text on target
8. Camera captures result
9. AI verifies action completed
10. All events logged to session log
```

**Pass Criteria**: ✅ Full approval → execution → verification cycle works

---

### 7.4. Emergency Stop Test

```
1. Execute mode enabled
2. Queue 5 actions (e.g., type 5 sentences)
3. Start execution
4. After 2 actions, operator toggles kill switch OFF
5. Verify: HID stops immediately
6. Verify: Pico W loses power
7. Verify: Target receives only 2 actions
8. Toggle kill switch ON
9. Verify: System recovers, mode resets to OBSERVE
```

**Pass Criteria**: ✅ Emergency stop interrupts execution safely

---

## Validation Checklist

### Hardware Assembly
- [ ] Kill switch inline with VBUS (not GPIO)
- [ ] LED wired to GPIO 2 with 330Ω resistor
- [ ] Camera positioned to view target screen
- [ ] All USB connections secure and labeled
- [ ] Power adapters UL listed or equivalent

### Firmware & Software
- [ ] CircuitPython 8.x flashed to Pico W
- [ ] HID executor firmware installed
- [ ] Brain dependencies installed (Python 3.11+, OpenCV, Tesseract)
- [ ] Contract validation tests pass (15/15)
- [ ] Camera detection test passes
- [ ] HID communication test passes

### Safety Mechanisms
- [ ] Kill switch removes power completely (SAFE-001)
- [ ] Kill switch stops action mid-execution (SAFE-002)
- [ ] Kill switch prevents reboot bypass (SAFE-003)
- [ ] Oversized commands rejected (BOUND-001)
- [ ] Rate limiting enforced (BOUND-002)
- [ ] HID disabled in non-EXECUTE modes (MODE-001)
- [ ] LED indicates mode correctly (MODE-002)

### Integration
- [ ] Brain → Camera communication works
- [ ] Brain → HID Executor serial communication works
- [ ] HID Executor → Target USB HID works
- [ ] Mode transitions successful
- [ ] Session logging functional

### Documentation
- [ ] All tests documented with results
- [ ] Failure modes identified and mitigated
- [ ] Operator trained on kill switch usage
- [ ] System limitations documented

---

## Troubleshooting Guide

### Issue: Pico W not detected
**Symptoms**: No /dev/ttyACM0 device
**Possible Causes**:
- CircuitPython not installed
- USB cable is charge-only (not data)
- Kill switch in OFF position
**Solutions**:
- Re-flash CircuitPython
- Use data-capable USB cable
- Toggle kill switch to ON

---

### Issue: LED does not illuminate
**Symptoms**: LED stays OFF even in EXECUTE mode
**Possible Causes**:
- LED polarity reversed
- Resistor wrong value or missing
- GPIO 2 not configured correctly
**Solutions**:
- Check LED flat side = cathode (to GND)
- Verify 330Ω resistor present
- Test GPIO with multimeter (should be 3.3V high)

---

### Issue: Camera not detected
**Symptoms**: No /dev/video0 device
**Possible Causes**:
- USB 2.0 port used (need USB 3.0)
- VM USB passthrough not configured
- Camera driver not loaded
**Solutions**:
- Use blue USB 3.0 port on RPi4
- Configure USB passthrough in Proxmox
- Run: `sudo modprobe uvcvideo`

---

### Issue: HID actions not working
**Symptoms**: Commands sent but nothing happens on target
**Possible Causes**:
- Mode not set to EXECUTE
- Kill switch in OFF position
- USB HID not recognized by target
**Solutions**:
- Verify mode = EXECUTE (LED should be ON)
- Toggle kill switch to ON
- Check target device manager (should see "HID Keyboard")

---

### Issue: Text typed incorrectly
**Symptoms**: Wrong characters appear on target
**Possible Causes**:
- Keyboard layout mismatch
- Contract validation failed
- Firmware bug
**Solutions**:
- Verify target uses US keyboard layout
- Check serial logs for validation errors
- Re-flash firmware if persistent

---

## Next Steps After Bring-Up

1. **Document baseline performance**
   - Capture latency (camera to AI)
   - Action execution latency (Brain to target)
   - Frame rate (fps achieved)

2. **Stress test system**
   - Long sessions (1+ hour)
   - Rapid mode transitions
   - Maximum text length commands

3. **Implement missing software**
   - AI engine module
   - Web UI control panel
   - Session logger with checksums

4. **Create operator training materials**
   - Quick start guide
   - Emergency procedures
   - Common workflows

5. **Establish maintenance schedule**
   - Weekly: Check logs for errors
   - Monthly: Verify kill switch function
   - Quarterly: Update software dependencies

---

**Bring-Up Completion Criteria**:
- ✅ All hardware components validated individually
- ✅ System integration successful
- ✅ Safety mechanisms tested and verified
- ✅ End-to-end workflows validated
- ✅ Documentation complete
- ✅ Operator trained

**Last Updated**: 2026-01-01  
**Next Review**: After first live session in lab
