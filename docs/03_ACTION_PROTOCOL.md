# Action Protocol (Approve / Execute)

## Action Types
- TYPE_TEXT (bounded)
- PRESS_KEYS (bounded combos)
- MOUSE_MOVE_CLICK (only after calibration; optional)

## Workflow
1) Assistant proposes action with rationale
2) User approves/denies
3) If approved, executor performs action
4) System records result + next observation

## Logging
- Proposed action
- Approved/denied
- Executed payload summary
- Timestamp + target profile
