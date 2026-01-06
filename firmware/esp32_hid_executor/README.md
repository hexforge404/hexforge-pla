# ESP32 HID Executor (S2/S3)

Minimal Arduino + TinyUSB scaffold for the PLA "hands". Targets ESP32-S2/S3 with native USB (CDC + HID).

## Safety rules (must keep)
- Requires ARM message over CDC _and_ physical arm switch (TODO: wire to GPIO and gate).
- Enforce `MIN_ACTION_DELAY_MS` and `MAX_TEXT` bounds for TYPE_TEXT.
- Reject messages that do not validate (missing execution_id, text, etc.).
- TODO: Implement LED/status heartbeat and periodic `device_status` JSON back to host.

## Building
```
pm install -g platformio
cd firmware/esp32_hid_executor
pio run -t upload
```

## Protocol (CDC, newline-delimited JSON)
- Host -> device: `{"type":"arm","enabled":true}`
- Host -> device: full `action_execute` payload (TYPE_TEXT only for now)
- Device -> host: `{"type":"ack","execution_id":"...","ok":true}` or `{"type":"err","message":"..."}`

## Next steps
- Implement proper JSON parsing and HID reports via TinyUSB keyboard/mouse.
- Add GPIO kill/arm switch, status LED, and periodic `device_status` emissions.
- Enforce allowed keycodes and rate limiting per contract.
