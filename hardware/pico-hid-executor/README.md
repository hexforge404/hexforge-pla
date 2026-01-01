# HID Executor Firmware — HexForge PLA

**Platform**: Raspberry Pi Pico W  
**Language**: CircuitPython 8.x  
**Purpose**: Bounded HID keyboard/mouse execution with hardware safety

---

## Features

- ✅ USB HID keyboard and mouse emulation
- ✅ Serial command interface (115200 baud)
- ✅ Mode-based safety (OBSERVE/SUGGEST/EXECUTE)
- ✅ Command bounds: max 1024 chars, rate limit 100ms
- ✅ Physical kill switch (VBUS interrupt)
- ✅ HID ARMED LED indicator
- ✅ Credential pattern rejection

---

## Hardware Requirements

- Raspberry Pi Pico W
- SPST toggle switch (kill switch, inline with VBUS)
- Red LED (5mm) + 220Ω resistor (HID ARMED indicator)
- USB-C cable (power + serial communication)

See [07_SETUP_HID_EXECUTOR.md](../../docs/07_SETUP_HID_EXECUTOR.md) for wiring diagrams.

---

## Firmware Installation

1. **Flash CircuitPython**:
   - Download `.uf2` from https://circuitpython.org/board/raspberry_pi_pico_w/
   - Hold BOOTSEL, connect USB, copy `.uf2` to RPI-RP2 drive

2. **Install Libraries**:
   ```bash
   # Download library bundle
   wget https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/latest/download/adafruit-circuitpython-bundle-8.x-mpy-*.zip
   unzip adafruit-circuitpython-bundle-*.zip
   
   # Copy HID library to Pico W
   cp -r adafruit-circuitpython-bundle-*/lib/adafruit_hid /media/CIRCUITPY/lib/
   ```

3. **Copy Firmware**:
   ```bash
   cp main.py /media/CIRCUITPY/main.py
   ```

4. **Reboot**: Pico W automatically runs `main.py` on boot

---

## Protocol

### Commands from Brain → HID Executor

```json
{"type": "set_mode", "mode": "OBSERVE|SUGGEST|EXECUTE"}
{"type": "type_text", "text": "Hello World"}
{"type": "key_combo", "keys": ["ctrl", "c"]}
{"type": "mouse_move", "x": 100, "y": 200}
{"type": "mouse_click", "button": "left"}
```

### Responses from HID Executor → Brain

```json
{"status": "ok", "action": "type_text"}
{"status": "error", "message": "Command rejected - text length exceeds MAX_TEXT_LENGTH"}
{"status": "error", "message": "HID disabled in OBSERVE mode"}
```

---

## Safety Bounds

| Bound | Value | Enforcement |
|-------|-------|-------------|
| MAX_TEXT_LENGTH | 1024 chars | Firmware rejects longer text |
| MIN_ACTION_DELAY_MS | 100 ms | Firmware enforces delay between actions |
| MODE_CHECK | Before every action | Firmware rejects HID if mode != EXECUTE |
| KILL_SWITCH | Hardware VBUS interrupt | Cannot be bypassed in software |

---

## LED Indicator

- **OFF**: HID disabled (mode = OBSERVE or SUGGEST)
- **ON**: HID armed (mode = EXECUTE)

---

## Testing

1. **Serial Monitor**:
   ```bash
   screen /dev/ttyACM0 115200
   # Or: python -m serial.tools.miniterm /dev/ttyACM0 115200
   ```

2. **Test Commands**:
   ```bash
   # Set mode to EXECUTE (LED should turn ON)
   echo '{"type":"set_mode","mode":"EXECUTE"}' > /dev/ttyACM0
   
   # Type text (should work in EXECUTE mode)
   echo '{"type":"type_text","text":"Hello from Pico W"}' > /dev/ttyACM0
   
   # Set mode to OBSERVE (LED should turn OFF)
   echo '{"type":"set_mode","mode":"OBSERVE"}' > /dev/ttyACM0
   
   # Try typing in OBSERVE mode (should be rejected)
   echo '{"type":"type_text","text":"This should fail"}' > /dev/ttyACM0
   ```

3. **Kill Switch Test**:
   - With Pico W powered and LED ON, toggle kill switch
   - Verify Pico W powers off completely
   - Toggle kill switch back on, verify Pico W reboots

---

## Troubleshooting

### Pico W Not Detected

```bash
lsusb | grep "Raspberry Pi"
# Should show: Bus 001 Device 005: ID 2e8a:0005 Raspberry Pi Pico W
```

### CircuitPython Not Running

- Check for `CIRCUITPY` USB drive when connected
- If shows `RPI-RP2` instead, re-flash CircuitPython `.uf2`
- Check `main.py` for syntax errors via serial console

### LED Not Working

- Check wiring: GPIO 2 → 220Ω resistor → LED anode (+) → LED cathode (-) → GND
- Test LED with multimeter (should have ~2V forward voltage)
- Verify polarity (long leg = anode, short leg = cathode)

---

**See also**:
- [Architecture: HID Executor](../../docs/01_ARCHITECTURE.md#hid-executor)
- [Setup HID Executor](../../docs/07_SETUP_HID_EXECUTOR.md)
- [Safety Guardrails](../../docs/02_SAFETY_GUARDRAILS.md)
