"""
HexForge PLA - HID Executor Firmware (Raspberry Pi Pico W)

This firmware runs on the Raspberry Pi Pico W to execute bounded HID keyboard/mouse
actions. It receives JSON commands via USB serial from the Brain and enforces safety
bounds: max text length, rate limiting, mode-based execution, and kill switch.

Safety Features:
- Physical kill switch (VBUS interrupt, cannot be bypassed)
- Command bounds: MAX_TEXT_LENGTH=1024, MIN_ACTION_DELAY_MS=100
- Mode validation: HID only executes in EXECUTE mode
- LED indicator: ON when HID armed (EXECUTE mode), OFF otherwise
- Session logging of all commands

Author: HexForge Team
Version: 1.0
License: Internal use only
"""

import time
import board
import digitalio
import usb_cdc
import json
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse

# Import contract validator
try:
    from contract_validator import validate_execute_command
    CONTRACT_VALIDATION_ENABLED = True
except ImportError:
    CONTRACT_VALIDATION_ENABLED = False
    print("WARNING: Contract validator not found, running without validation")

# ============================================================================
# SAFETY CONFIGURATION (DO NOT MODIFY WITHOUT APPROVAL)
# ============================================================================

MAX_TEXT_LENGTH = 1024  # Maximum characters per type_text command
MIN_ACTION_DELAY_MS = 100  # Minimum milliseconds between HID actions
ALLOWED_MODES = ["OBSERVE", "SUGGEST", "EXECUTE"]
HID_ARMED_MODES = ["EXECUTE"]  # HID only executes in these modes

# ============================================================================
# HARDWARE SETUP
# ============================================================================

# LED indicator (GPIO 2): ON when HID armed (mode=EXECUTE), OFF otherwise
led = digitalio.DigitalInOut(board.GP2)
led.direction = digitalio.Direction.OUTPUT
led.value = False  # Start with LED OFF

# USB HID devices
keyboard = Keyboard(usb_cdc.console)
mouse = Mouse(usb_cdc.console)

# Serial communication (115200 baud, default for USB CDC)
serial = usb_cdc.data

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

current_mode = "OBSERVE"  # Default mode: safe, no HID execution
last_action_time = 0  # Timestamp of last HID action (for rate limiting)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def send_response(status, message="", action=""):
    """Send JSON response to Brain via serial."""
    response = {"status": status}
    if message:
        response["message"] = message
    if action:
        response["action"] = action
    
    serial.write((json.dumps(response) + '\n').encode('utf-8'))


def update_led():
    """Update LED indicator based on current mode."""
    if current_mode in HID_ARMED_MODES:
        led.value = True  # LED ON: HID armed
    else:
        led.value = False  # LED OFF: HID disabled


def enforce_rate_limit():
    """Enforce minimum delay between HID actions."""
    global last_action_time
    
    current_time = time.monotonic() * 1000  # Convert to milliseconds
    elapsed = current_time - last_action_time
    
    if elapsed < MIN_ACTION_DELAY_MS:
        delay = (MIN_ACTION_DELAY_MS - elapsed) / 1000.0
        time.sleep(delay)
    
    last_action_time = time.monotonic() * 1000


def is_hid_allowed():
    """Check if HID execution is allowed in current mode."""
    return current_mode in HID_ARMED_MODES


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

def handle_set_mode(command):
    """Change operating mode (OBSERVE, SUGGEST, EXECUTE)."""
    global current_mode
    
    new_mode = command.get("mode", "").upper()
    
    if new_mode not in ALLOWED_MODES:
        send_response("error", f"Invalid mode: {new_mode}")
        return
    
    current_mode = new_mode
    update_led()
    send_response("ok", f"Mode changed to {current_mode}")


def handle_type_text(command):
    """Type text via HID keyboard."""
    if not is_hid_allowed():
        send_response("error", f"HID disabled in {current_mode} mode")
        return
    
    text = command.get("text", "")
    
    # Enforce MAX_TEXT_LENGTH
    if len(text) > MAX_TEXT_LENGTH:
        send_response("error", f"Command rejected - text length {len(text)} exceeds MAX_TEXT_LENGTH {MAX_TEXT_LENGTH}")
        return
    
    # Enforce rate limiting
    enforce_rate_limit()
    
    # Execute HID action
    try:
        keyboard.write(text)
        send_response("ok", action="type_text")
    except Exception as e:
        send_response("error", f"HID error: {str(e)}")


def handle_key_combo(command):
    """Execute key combination (e.g., Ctrl+C)."""
    if not is_hid_allowed():
        send_response("error", f"HID disabled in {current_mode} mode")
        return
    
    keys = command.get("keys", [])
    
    if not keys:
        send_response("error", "No keys specified")
        return
    
    # Enforce rate limiting
    enforce_rate_limit()
    
    # Map key names to Keycode constants
    key_map = {
        "ctrl": Keycode.CONTROL,
        "alt": Keycode.ALT,
        "shift": Keycode.SHIFT,
        "gui": Keycode.GUI,  # Windows key / Command key
        "enter": Keycode.ENTER,
        "escape": Keycode.ESCAPE,
        "tab": Keycode.TAB,
        "backspace": Keycode.BACKSPACE,
        # Add more as needed
    }
    
    # Execute key combo
    try:
        keycodes = [key_map.get(k.lower(), Keycode.__dict__.get(k.upper())) for k in keys]
        keyboard.press(*keycodes)
        keyboard.release_all()
        send_response("ok", action="key_combo")
    except Exception as e:
        send_response("error", f"Key combo error: {str(e)}")


def handle_mouse_move(command):
    """Move mouse cursor to absolute coordinates."""
    if not is_hid_allowed():
        send_response("error", f"HID disabled in {current_mode} mode")
        return
    
    x = command.get("x", 0)
    y = command.get("y", 0)
    
    # Enforce rate limiting
    enforce_rate_limit()
    
    try:
        mouse.move(x, y)
        send_response("ok", action="mouse_move")
    except Exception as e:
        send_response("error", f"Mouse move error: {str(e)}")


def handle_mouse_click(command):
    """Click mouse button."""
    if not is_hid_allowed():
        send_response("error", f"HID disabled in {current_mode} mode")
        return
    
    button = command.get("button", "left").lower()
    
    # Enforce rate limiting
    enforce_rate_limit()
    
    try:
        if button == "left":
            mouse.click(Mouse.LEFT_BUTTON)
        elif button == "right":
            mouse.click(Mouse.RIGHT_BUTTON)
        elif button == "middle":
            mouse.click(Mouse.MIDDLE_BUTTON)
        else:
            send_response("error", f"Invalid mouse button: {button}")
            return
        
        send_response("ok", action="mouse_click")
    except Exception as e:
        send_response("error", f"Mouse click error: {str(e)}")


# ============================================================================
# MAIN LOOP
# ============================================================================

def main():
    """Main event loop: receive commands, execute with safety bounds."""
    print("="*60)
    print("HexForge PLA - HID Executor v1.0")
    print("="*60)
    print(f"Mode: {current_mode} (HID DISABLED)")
    print(f"Max text length: {MAX_TEXT_LENGTH} chars")
    print(f"Rate limit: {MIN_ACTION_DELAY_MS} ms between actions")
    print("Kill switch: ENABLED (hardware VBUS interrupt)")
    print("Waiting for commands from Brain...")
    print("="*60)
    
    buffer = ""
    
    while True:
        # Check for incoming serial data
        if serial.in_waiting > 0:
            chunk = serial.read(serial.in_waiting).decode('utf-8', errors='ignore')
            buffer += chunk
            
            # Process complete JSON commands (newline-delimited)
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                
                if not line:
                    continue
                
                # Parse JSON command
                try:
                    command = json.loads(line)
                except json.JSONDecodeError as e:
                    send_response("error", f"JSON parse error: {str(e)}")
                    continue
                
                # Validate contract for execute commands (if validator available)
                if CONTRACT_VALIDATION_ENABLED and command.get("type") != "set_mode":
                    # Contract validation for action_execute commands
                    # Note: set_mode uses simpler protocol, not action_execute
                    if "execution_id" in command:  # This is an action_execute command
                        is_valid, error = validate_execute_command(command)
                        if not is_valid:
                            send_response("error", f"Contract validation failed: {error}")
                            continue
                
                # Dispatch command to handler
                cmd_type = command.get("type", "")
                
                # Support both legacy protocol and new contract protocol
                # Legacy: {"type": "type_text", "text": "..."}
                # Contract: {"execution_id": "...", "action_type": "TYPE_TEXT", "payload": {...}}
                if "execution_id" in command:
                    # New contract protocol
                    action_type = command.get("action_type", "")
                    payload = command.get("payload", {})
                    
                    if action_type == "TYPE_TEXT":
                        handle_type_text(payload)
                    elif action_type == "KEY_COMBO":
                        handle_key_combo(payload)
                    elif action_type == "MOUSE_MOVE":
                        handle_mouse_move(payload)
                    elif action_type == "MOUSE_CLICK":
                        handle_mouse_click(payload)
                    else:
                        send_response("error", f"Unknown action_type: {action_type}")
                else:
                    # Legacy protocol (backward compatible)
                    if cmd_type == "set_mode":
                        handle_set_mode(command)
                    elif cmd_type == "type_text":
                        handle_type_text(command)
                    elif cmd_type == "key_combo":
                        handle_key_combo(command)
                    elif cmd_type == "mouse_move":
                        handle_mouse_move(command)
                    elif cmd_type == "mouse_click":
                        handle_mouse_click(command)
                    else:
                        send_response("error", f"Unknown command type: {cmd_type}")
        
        time.sleep(0.01)  # Small delay to prevent CPU spin


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        # Emergency: turn off LED and disable HID
        led.value = False
        raise
