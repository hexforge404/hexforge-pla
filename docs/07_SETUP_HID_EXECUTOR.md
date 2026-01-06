echo '{"type":"set_mode","mode":"SUGGEST"}' > /dev/ttyACM0
echo '{"type":"set_mode","mode":"EXECUTE"}' > /dev/ttyACM0
echo '{"type":"type_text","text":"'$(python3 -c 'print("A"*2000)')'"}' > /dev/ttyACM0
dmesg | tail -20
# Setup Guide: ESP32 HID Executor — HexForge PLA

**Goal:** Wire and flash the ESP32 HID executor with physical interlocks (kill switch, armed LED) so HID can only operate when physically enabled. The Brain (Pi/VM) never drives HID directly.

**Valid MCU Variants**
- ESP32-S2 or ESP32-S3 with native USB (CDC + HID) and TinyUSB support.
- Dev boards with USB-OTG port exposed (e.g., ESP32-S2-Saola, ESP32-S3-DevKitC-1). Avoid classic ESP32/ESP32-C3 (no native USB HID) and Pico/Pico W.

**Firmware Assumptions**
- Arduino + TinyUSB **or** ESP-IDF TinyUSB class driver.
- HID reports (keyboard + mouse) and CDC for status/commands.
- Matches PLA contract bounds: max text 1024, min action spacing 100 ms, heartbeat device_status.

---

## Bill of Materials (per executor)
- ESP32-S2 or ESP32-S3 dev board with native USB (USB-C preferred)
- USB host cable from Brain → ESP32 (data + power)
- SPST kill switch rated ≥5 V / 500 mA (panel toggle or rocker)
- Red LED ("HID ARMED") + 220 Ω resistor
- Optional: momentary button for physical arm input (GPIO)
- Heat-shrink, hookup wire, enclosure, and labels for safety

---

## Wiring Overview (Safety-First)
- **Kill switch in series with USB VBUS** from Brain to ESP32; removes power so firmware cannot bypass.
- **Armed LED** on ESP32 GPIO to surface armed state visibly.
- **Optional physical arm button** to feed a GPIO that firmware AND host check before enabling EXECUTE.

### Kill Switch (VBUS Cut)
```
Host USB (Brain) ----[ +5V (red) ]----[ SPST Kill Switch ]----> ESP32 VBUS
Host GND  -----------------------------------------------> ESP32 GND
D+ / D- (data) ------------------------------------------> ESP32 D+ / D-
```
- Cut the +5 V wire (red) in the USB cable or use a USB breakout; place switch in series.
- Do **not** switch data lines; only VBUS. Insulate all splices.
- Verify with multimeter: OFF = open circuit between host VBUS and ESP32 VBUS.

### Armed LED (example GPIO 5)
```
ESP32 GPIO5 ----[220Ω]----|> (LED Anode)
LED Cathode ----------------------- GND
```
- LED must be visible on the enclosure front. High = armed.
- GPIO number is configurable; keep it in config (`arm_gpio`, default 5).

### Optional Physical Arm Button (example GPIO 4)
```
3V3 ----[10k]----+----> GPIO4 (input, pull-up)
                 |
             [Momentary NO Button]
                 |
                GND
```
- Button pulls GPIO4 low when pressed/latched; firmware reads as "physical_ok".
- If unused, leave disabled in firmware/config.

---

## Step-by-Step Wiring (ESP32-S2/S3)
1. **Prepare USB lead**: cut a spare USB cable; expose red (+5 V), black (GND), green (D+), white (D-).
2. **Insert kill switch** in series with the red wire; insulate joints.
3. **Connect data and ground** directly: green→D+, white→D-, black→GND.
4. **LED**: connect GPIO5 → 220 Ω → LED anode; LED cathode → GND. Label "HID ARMED".
5. **Optional arm button**: wire GPIO4 with pull-up to 3V3 and button to GND as shown above.
6. Mount switch and LED on enclosure; ensure clear visibility and tactile switch action.
7. Continuity check: switch OFF = no power to ESP32; switch ON = ESP32 enumerates over USB.

---

## Firmware Flash (Arduino TinyUSB)
1. Install ESP32 boards package (ESP32 3.x) in Arduino IDE.
2. Select board: **ESP32S3 Dev Module** (or ESP32S2 equivalent). Enable TinyUSB CDC + HID.
3. Set USB mode to "CDC and HID"; upload firmware from `esp32_firmware/`.
4. Confirm serial at 115200 baud and HID descriptors present (check `dmesg` or `lsusb`).

(ESP-IDF users: configure TinyUSB CDC+HID composite, enable VBUS sense if available.)

---

## Validation Checklist
- **Power cut**: Toggle kill switch OFF → ESP32 powers down and disconnects from USB; ON → enumerates.
- **LED**: Arms only when host sets EXECUTE; stays off in OBSERVE/SUGGEST.
- **Physical arm**: If wired, EXECUTE is blocked unless button/pull-up reports OK.
- **Contract bounds**: Typing >1024 chars or key combos outside allowed set must be rejected by firmware/host.
- **Heartbeat**: device_status emitted periodically; host refuses commands if stale.

---

## Safety Rules (Do Not Violate)
- Never bypass the kill switch (no always-on VBUS, no firmware-only disable).
- LED must be visible to the operator; do not bury inside enclosure.
- Do not power ESP32 from a separate supply during HID use; the kill switch must remove **all** HID power.
- Do not reroute host data through relays/switches; only VBUS is switchable to avoid signal integrity loss.
- Brain and Hands stay separate: Brain sends bounded contracts; ESP32 executes only after physical + logical arm.

---

## Quick Reference
- Kill switch: in-series with USB +5 V between Brain and ESP32.
- Armed LED: GPIO5 → 220 Ω → LED → GND (configurable `arm_gpio`).
- Optional arm input: GPIO4 pull-up to 3V3, button to GND.
- Valid MCUs: ESP32-S2 / ESP32-S3 with native USB; no Pico, no classic ESP32.
- Firmware stack: TinyUSB composite (CDC + HID), respects PLA contracts and heartbeats.
