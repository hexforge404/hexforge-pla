# ESP32 Hands-On MVP Firmware

Minimal PlatformIO Arduino firmware to send button press events from an ESP32-WROOM dev board to the PLA Node over Wi-Fi.

## Wiring (text diagram)
- GPIO4 -> momentary button -> GND (use INPUT_PULLUP)
- GPIO2 -> onboard LED -> GND (active LOW; no resistor available)
- 5V/3V3 and GND as per your board’s power requirements

## Files
- platformio.ini — PlatformIO config (board esp32dev, Arduino, 115200 baud)
- src/main.cpp — firmware
- include/secrets.h — Wi-Fi + PLA Node settings (gitignored)

## Setup
1. Install PlatformIO (VS Code extension or CLI).
2. Copy include/secrets.h and fill in WIFI_SSID/PASS. Adjust PLA_HOST/PLA_PORT if needed; leave PLA_API_KEY empty unless PLA Node requires it.
3. Connect the ESP32 over USB.

## Flash
```
cd esp32_firmware
pio run -t upload
pio device monitor -b 115200
```

## Behavior
- Boot: LED slow-blinks while connecting to Wi-Fi and until PLA Node health check passes.
- Ready: LED solid ON after successful health check.
- Button press (GPIO4 to GND): sends POST to http://PLA_HOST:PLA_PORT/ingest with payload:
  {
    "event_version": "1.0",
    "device_id": "esp32-hands-001",
    "event_type": "button_press",
    "ts_ms": <millis>
  }
- Success: LED quick flash.
- Failure: LED triple flash.
- Serial logs: Wi-Fi status/IP, health check status and body, ingest status and body.

## Test steps (end-to-end)
1. Power the ESP32; open serial monitor at 115200.
2. Confirm Wi-Fi connection log and PLA health check OK; LED should go solid.
3. Press the button (GPIO4->GND).
4. Observe serial output for ingest status 202/200 and response body; LED should quick flash.
5. On PLA Node (at 10.0.0.22), check logs/events.ndjson for the new event with device_id esp32-hands-001.

## Notes
- Core split: button handling runs in a FreeRTOS task on core 1; Wi-Fi/HTTP run on the main (core 0) loop.
- If Wi-Fi or health fails at boot, the firmware keeps blinking and retries; a hard failure after ~40s Wi-Fi wait triggers a reboot.
