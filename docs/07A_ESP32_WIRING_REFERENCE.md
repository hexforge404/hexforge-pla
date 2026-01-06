# ESP32 HID Executor Wiring Reference — HexForge PLA

Use this as a quick pinout and wiring checklist. All wiring must preserve the physical kill switch and visible armed indicator. Brain (Pi/VM) only sends bounded contracts; ESP32 executes.

## Required Connections
- **USB from Brain → ESP32**: D+, D-, GND direct; +5 V routed through kill switch.
- **Kill Switch (mandatory)**: In series with USB +5 V (VBUS). OFF removes all HID power.
- **Armed LED (mandatory)**: ESP32 GPIO → 220 Ω → LED → GND. Visible on enclosure front.
- **Ground**: Common GND between host and ESP32.

## Example Pin Assignments (configurable)
- Kill switch: inline with USB VBUS (no GPIO).
- Armed LED: GPIO5 → 220 Ω → LED → GND (`arm_gpio` default 5).
- Optional physical arm button: GPIO4 with pull-up to 3V3, button to GND (reads low when pressed).

## ASCII Reference
```
Host USB
  +5V ----[Kill Switch]-------------------> ESP32 VBUS
  D+  ------------------------------------> ESP32 D+
  D-  ------------------------------------> ESP32 D-
  GND ------------------------------------> ESP32 GND

Armed LED
  ESP32 GPIO5 ----[220Ω]----|>---- GND

Optional Arm Button
  3V3 ---[10k]---+----> GPIO4
                 |
             [Button]
                 |
                GND
```

## Safety Notes
- Never bypass the kill switch; do not power ESP32 from alternate supplies during HID use.
- LED must be operator-visible; burying it defeats armed-state visibility.
- Do not switch data lines; only VBUS is switched to avoid USB signal issues.
- ESP32-S2/S3 with native USB only; classic ESP32 variants are invalid for HID here.
