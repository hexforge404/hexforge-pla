# Safety Guardrails

## Required
- Physical kill switch that removes power to HID device
- Visible "HID ARMED" indicator
- Default mode: Confirm-to-execute
- All actions logged with timestamps

## Action Constraints
- Bounded keystroke length per action
- Rate limit between actions
- No freeform macros without re-confirmation
