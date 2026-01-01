# Setup Guide: HID Executor (Raspberry Pi Pico W) — HexForge PLA

**Goal**: Flash firmware, wire kill switch, and test bounded HID execution  
**Estimated Time**: 1-2 hours  
**Skill Level**: Intermediate (basic electronics soldering required)

---

## Bill of Materials

| Component | Qty | Purpose | Cost |
|-----------|-----|---------|------|
| Raspberry Pi Pico W | 1 | HID executor microcontroller | $6 |
| SPST Kill Switch (toggle) | 1 | Emergency stop for HID | $8 |
| Red LED (5mm) | 1 | "HID ARMED" indicator | $1 |
| 220Ω Resistor | 1 | LED current limiter | $0.50 |
| USB-C cable (for Pico W) | 1 | Power + serial communication | $5 |
| Jumper wires / breadboard | - | Prototyping connections | $5 |
| Enclosure (optional) | 1 | Safety housing | $10 |

**Total**: ~$36

---

## Phase 1: Firmware Setup

### Install CircuitPython on Pico W

1. Download CircuitPython `.uf2` file:
   - Visit https://circuitpython.org/board/raspberry_pi_pico_w/
   - Download latest stable release (8.x or newer)

2. Enter bootloader mode:
   - Hold **BOOTSEL** button on Pico W
   - Connect USB cable to computer
   - Release **BOOTSEL**
   - Pico W mounts as `RPI-RP2` USB drive

3. Flash firmware:
   ```bash
   # Copy .uf2 file to mounted drive
   cp ~/Downloads/adafruit-circuitpython-raspberry_pi_pico_w-*.uf2 /media/RPI-RP2/
   ```

4. Pico W reboots and remounts as `CIRCUITPY` drive

### Install Required Libraries

```bash
# Download CircuitPython library bundle
wget https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/latest/download/adafruit-circuitpython-bundle-8.x-mpy-*.zip
unzip adafruit-circuitpython-bundle-*.zip

# Copy HID library to Pico W
cp -r adafruit-circuitpython-bundle-*/lib/adafruit_hid /media/CIRCUITPY/lib/
```

---

## Phase 2: Wiring Diagrams

### Kill Switch (VBUS Interrupt)

**Purpose**: Physically cuts USB power to disable HID, cannot be bypassed in software.

```
USB-C Cable (from Brain to Pico W):
┌─────────────────┐
│  USB-C Plug     │──┐
│  (from Brain)   │  │
└─────────────────┘  │
                     │ VBUS (red wire)
                     │
                     ├──[SPST Kill Switch]──┐
                     │                      │
┌─────────────────┐  │                      │
│  Raspberry Pi   │  │                      │
│  Pico W         │<─┴──────────────────────┘
│                 │
│  GPIO 2 ────────┼──[220Ω Resistor]──[LED+]──[LED-]──GND
│  (LED control)  │
└─────────────────┘
```

**Assembly Steps**:
1. Cut USB cable between Brain and Pico W (or use USB breakout board)
2. Identify VBUS (red wire, typically +5V)
3. Solder kill switch in series with VBUS
4. Use heat shrink tubing to insulate connections
5. **Test switch**: Ensure toggling switch powers Pico on/off

### HID ARMED LED

```
Pico W GPIO 2 ──┬── [220Ω Resistor] ──┬── LED (Anode +)
                │                     │
                │                     └── LED (Cathode -)
                │                              │
                └─────────────── GND ──────────┘
```

**Assembly**:
- Connect GPIO 2 to LED anode (long leg) via 220Ω resistor
- Connect LED cathode (short leg) to GND
- LED lights when HID mode is ARMED (mode != OBSERVE)

---

## Phase 3: Firmware Installation

Copy the main firmware to Pico W:

```bash
# From hardware/pico-hid-executor/ directory
cp main.py /media/CIRCUITPY/main.py
cp config.py /media/CIRCUITPY/config.py  # If using separate config
```

Firmware automatically runs on boot. Check serial output:

```bash
# Linux/Mac
screen /dev/ttyACM0 115200

# Or use Python serial monitor
python -m serial.tools.miniterm /dev/ttyACM0 115200
```

**Expected Boot Messages**:
```
HID Executor v1.0 - HexForge PLA
Mode: OBSERVE (HID DISABLED)
Kill switch: ENABLED
Waiting for commands from Brain...
```

---

## Phase 4: Safety Testing

### Test 1: Kill Switch Function

```bash
# With Pico W powered on and LED lit:
1. Toggle kill switch to OFF
2. Verify Pico W powers down completely
3. Verify LED turns off
4. Toggle kill switch to ON
5. Verify Pico W reboots
```

**Pass Criteria**: Pico W must power off immediately when switch is toggled. No partial power state allowed.

### Test 2: Mode Transition LED

```bash
# Send mode change command from Brain
echo '{"type":"set_mode","mode":"SUGGEST"}' > /dev/ttyACM0

# LED should remain OFF (SUGGEST mode does not ARM HID)

echo '{"type":"set_mode","mode":"EXECUTE"}' > /dev/ttyACM0

# LED should turn ON (EXECUTE mode ARMS HID)
```

**Pass Criteria**: LED lights ONLY when mode is EXECUTE.

### Test 3: Command Bounds Enforcement

```bash
# Send oversized command (>1024 chars)
echo '{"type":"type_text","text":"'$(python3 -c 'print("A"*2000)')'"}' > /dev/ttyACM0

# Check serial output for error:
# "ERROR: Command rejected - text length 2000 exceeds MAX_TEXT_LENGTH 1024"
```

**Pass Criteria**: Executor rejects command and logs error. No text typed.

### Test 4: Rate Limiting

```bash
# Send rapid commands (< 100ms apart)
for i in {1..10}; do
  echo '{"type":"type_text","text":"Test"}' > /dev/ttyACM0
done

# Check serial output - should enforce 100ms delay between actions
```

**Pass Criteria**: Commands processed with minimum 100ms spacing, even if sent faster.

---

## Phase 5: Integration with Brain

1. Connect Pico W to Brain VM via USB
2. Verify serial device appears:
   ```bash
   ls -l /dev/ttyACM0
   ```
3. Run Brain integration test:
   ```bash
   cd ~/hexforge-pla/software/brain
   source venv/bin/activate
   python test_hid_executor.py
   ```

**Expected Output**:
```
HID Executor detected at /dev/ttyACM0
Mode: OBSERVE
Setting mode to EXECUTE...
Mode changed: EXECUTE (LED ON)
Sending test command: {"type":"type_text","text":"Hello"}
Response: {"status":"ok","action":"type_text"}
Test passed.
```

---

## Troubleshooting

### Pico W Not Detected

```bash
# Check USB connection
lsusb | grep "Raspberry Pi"

# Check kernel messages
dmesg | tail -20
```

### CircuitPython Not Booting

- Re-flash `.uf2` file (hold BOOTSEL, reconnect USB)
- Check for `code.py` or `main.py` syntax errors via serial console

### Kill Switch Not Working

- Verify switch is in series with VBUS (not GND or signal wire)
- Test switch continuity with multimeter
- Ensure switch is rated for 5V 500mA minimum

---

**See also**:
- [Architecture: HID Executor](01_ARCHITECTURE.md#hid-executor)
- [Safety Guardrails](02_SAFETY_GUARDRAILS.md)
- [Test Plans: HID Safety Tests](08_TEST_PLANS.md#phase-2-safety-mechanism-tests)
- [Hardware BOM](04_HARDWARE_BOM.md)
