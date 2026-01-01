"""
Lightweight Contract Validator for HID Executor (CircuitPython)

Since CircuitPython doesn't have jsonschema, this provides minimal validation
for action_execute commands to enforce safety bounds.
"""


def validate_execute_command(cmd):
    """
    Validate action_execute command against contract requirements.
    
    Args:
        cmd (dict): Execute command to validate
        
    Returns:
        (bool, str|None): (is_valid, error_message)
    """
    # Check required fields
    required_fields = [
        'execution_id',
        'proposal_id',
        'timestamp',
        'mode',
        'action_type',
        'payload',
        'safety_bounds'
    ]
    
    for field in required_fields:
        if field not in cmd:
            return False, f"Missing required field: {field}"
    
    # Validate mode (MUST be EXECUTE for HID actions)
    if cmd['mode'] != 'EXECUTE':
        return False, f"Invalid mode: {cmd['mode']} (HID only in EXECUTE mode)"
    
    # Validate action_type
    valid_action_types = ['TYPE_TEXT', 'KEY_COMBO', 'MOUSE_MOVE', 'MOUSE_CLICK']
    if cmd['action_type'] not in valid_action_types:
        return False, f"Invalid action_type: {cmd['action_type']}"
    
    # Validate safety_bounds
    safety_bounds = cmd.get('safety_bounds', {})
    if safety_bounds.get('max_text_length') != 1024:
        return False, "safety_bounds.max_text_length must be 1024"
    if safety_bounds.get('min_action_delay_ms') != 100:
        return False, "safety_bounds.min_action_delay_ms must be 100"
    
    # Validate payload based on action_type
    payload = cmd.get('payload', {})
    
    if cmd['action_type'] == 'TYPE_TEXT':
        if 'text' not in payload:
            return False, "TYPE_TEXT requires 'text' in payload"
        
        text_len = len(payload['text'])
        if text_len > 1024:
            return False, f"Text length {text_len} exceeds MAX_TEXT_LENGTH (1024)"
    
    elif cmd['action_type'] == 'KEY_COMBO':
        if 'keys' not in payload:
            return False, "KEY_COMBO requires 'keys' in payload"
        
        if not isinstance(payload['keys'], list):
            return False, "KEY_COMBO 'keys' must be a list"
        
        if len(payload['keys']) < 1 or len(payload['keys']) > 5:
            return False, "KEY_COMBO must have 1-5 keys"
    
    elif cmd['action_type'] == 'MOUSE_MOVE':
        if 'x' not in payload or 'y' not in payload:
            return False, "MOUSE_MOVE requires 'x' and 'y' in payload"
        
        if not isinstance(payload['x'], int) or not isinstance(payload['y'], int):
            return False, "MOUSE_MOVE x and y must be integers"
    
    elif cmd['action_type'] == 'MOUSE_CLICK':
        if 'button' not in payload:
            return False, "MOUSE_CLICK requires 'button' in payload"
        
        if payload['button'] not in ['left', 'right', 'middle']:
            return False, f"Invalid button: {payload['button']}"
    
    # All validations passed
    return True, None


def validate_device_status(status):
    """
    Validate device_status report against contract requirements.
    
    Args:
        status (dict): Device status to validate
        
    Returns:
        (bool, str|None): (is_valid, error_message)
    """
    # Check required fields
    required_fields = [
        'device_id',
        'timestamp',
        'mode',
        'led_state',
        'kill_switch_state',
        'uptime_seconds'
    ]
    
    for field in required_fields:
        if field not in status:
            return False, f"Missing required field: {field}"
    
    # Validate mode
    if status['mode'] not in ['OBSERVE', 'SUGGEST', 'EXECUTE']:
        return False, f"Invalid mode: {status['mode']}"
    
    # Validate led_state
    if not isinstance(status['led_state'], bool):
        return False, "led_state must be boolean"
    
    # Validate kill_switch_state
    if status['kill_switch_state'] not in ['ARMED', 'DISABLED', 'UNKNOWN']:
        return False, f"Invalid kill_switch_state: {status['kill_switch_state']}"
    
    # Validate uptime_seconds
    if not isinstance(status['uptime_seconds'], int) or status['uptime_seconds'] < 0:
        return False, "uptime_seconds must be non-negative integer"
    
    # All validations passed
    return True, None
