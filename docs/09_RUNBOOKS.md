# Runbooks & Operations — HexForge PLA

**Purpose**: Standard operating procedures and troubleshooting guides for daily use.

---

## Daily Operations

### Startup Sequence

1. **Power on Brain VM** (Proxmox or standalone RPi4)
   ```bash
   # Proxmox: Start VM
   qm start 200
   
   # SSH into Brain
   ssh plabrain@<VM_IP>
   ```

2. **Verify Camera Connection**
   ```bash
   ls -l /dev/video0
   v4l2-ctl --list-devices
   ```

3. **Connect HID Executor** (Raspberry Pi Pico W)
   - Ensure kill switch is in OFF position
   - Connect USB cable from Brain to Pico W
   - Toggle kill switch to ON
   - Verify device detected:
     ```bash
     ls -l /dev/ttyACM0
     dmesg | grep -i pico
     ```
   - Confirm LED is OFF (OBSERVE mode on boot)

4. **Start Brain Service**
   ```bash
   cd ~/hexforge-pla/software/brain
   source venv/bin/activate
   python src/main.py
   ```

5. **Verify System Status**
   - Check web UI at `http://<VM_IP>:5000`
   - Confirm camera feed visible
   - Confirm mode displays "OBSERVE"
   - Confirm HID executor shows "CONNECTED"

### Shutdown Sequence

1. **Set mode to OBSERVE**
   ```bash
   # Via web UI or CLI
   curl -X POST http://localhost:5000/api/mode -d '{"mode":"OBSERVE"}'
   ```

2. **Verify HID LED is OFF**

3. **Stop Brain Service**
   ```bash
   # Ctrl+C in terminal or:
   sudo systemctl stop hexforge-pla-brain
   ```

4. **Disconnect HID Executor**
   - Toggle kill switch to OFF
   - Unplug USB cable

5. **Shutdown Brain VM**
   ```bash
   sudo shutdown -h now
   ```

---

## Operating Mode Workflows

### OBSERVE Mode (Default)

**Purpose**: Passive monitoring, no HID actions.

1. Start system (follows startup sequence above)
2. Verify mode: `OBSERVE`
3. Brain captures screen every 2 seconds
4. OCR extracts text from camera feed
5. AI analyzes screen state, logs observations
6. **No HID actions executed**
7. Operator reviews AI observations in web UI

**Use Case**: Initial reconnaissance, understanding target system state without interaction.

---

### SUGGEST Mode (Operator-Approved Actions)

**Purpose**: AI suggests actions, operator approves each one.

1. **Transition to SUGGEST mode**:
   ```bash
   curl -X POST http://localhost:5000/api/mode -d '{"mode":"SUGGEST"}'
   ```
   - Verify LED remains OFF (HID still disarmed)

2. **AI analyzes screen and suggests action**:
   - Example: "Detected login prompt. Suggest typing username: `testuser`"
   - Suggestion appears in web UI

3. **Operator reviews suggestion**:
   - Read suggestion carefully
   - Verify action is safe and intended
   - Check for credential exposure risks

4. **Operator approves or rejects**:
   - Click "APPROVE" → Brain sends command to HID executor
   - Click "REJECT" → AI logs rejection, suggests alternative

5. **HID executes approved action**:
   - LED turns ON briefly during execution
   - Action logged to session log
   - LED turns OFF after completion

6. **Repeat for each action**

**Use Case**: Step-by-step automation with human oversight. Safest semi-automated mode.

---

### EXECUTE Mode (Manual Approval Required)

**Purpose**: AI executes actions after operator approval, but allows batch approval for workflows.

**⚠️ WARNING**: This mode arms HID executor. Use only in controlled sandbox environments.

1. **Transition to EXECUTE mode**:
   ```bash
   curl -X POST http://localhost:5000/api/mode -d '{"mode":"EXECUTE"}'
   ```
   - **LED turns ON** (HID executor armed)

2. **AI suggests action**:
   - Same as SUGGEST mode, but operator can approve multiple actions in advance

3. **Operator provides workflow approval**:
   - Example: "Approve next 5 actions for login workflow"
   - Brain queues approved actions

4. **AI executes workflow**:
   - Brain sends actions to HID executor sequentially
   - Rate limited to 100ms between actions
   - LED remains ON during execution

5. **Monitor execution**:
   - Watch target screen for unexpected behavior
   - **Keep hand on kill switch** during execution

6. **Emergency stop if needed**:
   - Toggle kill switch to OFF immediately
   - Review session logs to understand what executed

**Use Case**: Batch automation of repetitive tasks (e.g., form filling, configuration wizards). Requires constant operator supervision.

---

## Troubleshooting

### Camera Not Detecting Screen Changes

**Symptoms**: OCR returns same text repeatedly, no screen updates detected.

**Causes**:
- Camera autofocus hunting
- Incorrect camera positioning
- Screen glare/reflection
- Low contrast (dark room)

**Solutions**:
1. Disable autofocus:
   ```bash
   v4l2-ctl -d /dev/video0 --set-ctrl=focus_auto=0
   v4l2-ctl -d /dev/video0 --set-ctrl=focus_absolute=10
   ```
2. Adjust camera position (12-18" from screen, centered)
3. Increase room lighting, reduce screen brightness
4. Test frame capture manually:
   ```bash
   fswebcam -r 1920x1080 -d /dev/video0 /tmp/test.jpg
   tesseract /tmp/test.jpg stdout
   ```

---

### HID Executor Not Responding

**Symptoms**: Brain logs "HID executor timeout" or "No response from /dev/ttyACM0".

**Causes**:
- Kill switch in OFF position
- USB cable disconnected
- Pico W firmware crash
- Serial port locked by another process

**Solutions**:
1. Check kill switch position (must be ON)
2. Verify USB connection:
   ```bash
   lsusb | grep "Raspberry Pi"
   ls -l /dev/ttyACM0
   ```
3. Restart Pico W (toggle kill switch OFF then ON)
4. Check for serial port conflicts:
   ```bash
   sudo lsof | grep ttyACM0
   # Kill conflicting process if found
   ```
5. Reflash firmware if crash persists:
   - Hold BOOTSEL, connect USB, copy `main.py` to CIRCUITPY

---

### AI Suggesting Incorrect Actions

**Symptoms**: AI recommends actions that don't match screen state or are unsafe.

**Causes**:
- OCR misreading text
- AI model hallucination
- Insufficient context from screen
- Prompt injection attack

**Solutions**:
1. **Never approve actions you don't understand**
2. Review OCR output in web UI:
   ```bash
   curl http://localhost:5000/api/ocr_output
   ```
3. Improve OCR accuracy (see Camera Troubleshooting)
4. Check for suspicious text on screen (e.g., "Ignore previous instructions...")
5. If persistent, switch to OBSERVE mode and investigate:
   ```bash
   curl -X POST http://localhost:5000/api/mode -d '{"mode":"OBSERVE"}'
   ```

---

### Mode Stuck in EXECUTE

**Symptoms**: Cannot switch from EXECUTE to OBSERVE/SUGGEST, LED remains ON.

**Causes**:
- Pending HID actions in queue
- Brain service frozen
- Kill switch failure (rare)

**Solutions**:
1. **Immediate**: Toggle kill switch to OFF (forces HID disarm)
2. Check pending actions:
   ```bash
   curl http://localhost:5000/api/queue
   ```
3. Force mode change:
   ```bash
   curl -X POST http://localhost:5000/api/mode -d '{"mode":"OBSERVE","force":true}'
   ```
4. Restart Brain service:
   ```bash
   sudo systemctl restart hexforge-pla-brain
   ```
5. If LED still ON after service restart: **Kill switch is faulty, do not use HID executor until fixed.**

---

### Session Log Not Recording

**Symptoms**: `/var/log/hexforge-pla/sessions/` empty or logs missing recent actions.

**Causes**:
- Disk full
- Permission issues
- Logging disabled in config

**Solutions**:
1. Check disk space:
   ```bash
   df -h /var/log
   ```
2. Check permissions:
   ```bash
   ls -ld /var/log/hexforge-pla/sessions/
   sudo chown -R plabrain:plabrain /var/log/hexforge-pla/
   ```
3. Verify logging enabled in `config/brain_config.yaml`:
   ```yaml
   safety:
     session_logging: true
   ```
4. Restart Brain service to reinitialize logging

---

### Pico W LED Always OFF (Even in EXECUTE Mode)

**Symptoms**: LED never lights, even when mode=EXECUTE.

**Causes**:
- LED wired incorrectly (polarity reversed)
- Burnt out LED
- GPIO 2 not configured in firmware

**Solutions**:
1. Check wiring (see [Setup HID Executor](07_SETUP_HID_EXECUTOR.md#hid-armed-led))
2. Test LED with multimeter (should have ~2V forward voltage drop)
3. Verify firmware sets GPIO 2 HIGH in EXECUTE mode:
   ```python
   # In main.py on Pico W
   led.value = True  # Should light LED when mode=EXECUTE
   ```
4. Replace LED if burnt out

---

### Target System Not Accepting Keystrokes

**Symptoms**: HID executor logs success, but target system shows no typed text.

**Causes**:
- Target system keyboard focus not on input field
- USB HID not recognized by target OS
- Keyboard layout mismatch
- Anti-keylogger software blocking input

**Solutions**:
1. Verify target system has active input field (click text box manually)
2. Check USB HID device recognized on target:
   - Windows: Device Manager → Human Interface Devices
   - Linux: `lsusb | grep "Pico"`
3. Test with simple command:
   ```bash
   echo '{"type":"type_text","text":"test"}' > /dev/ttyACM0
   ```
4. If target has anti-keylogger: Whitelist Pico W USB VID:PID in security software

---

### Credential Detected by AI, But Action Still Approved

**Symptoms**: AI flagged potential credential in OCR, but operator accidentally approved action.

**Causes**:
- Operator error (clicked approve too quickly)
- Credential detection pattern too broad (false positive)

**Solutions**:
1. **Immediately**: Toggle kill switch to OFF
2. Review session logs to see what was typed:
   ```bash
   tail -50 /var/log/hexforge-pla/sessions/$(ls -t /var/log/hexforge-pla/sessions/ | head -1)
   ```
3. If credential was typed: **Rotate credential immediately**
4. Improve credential detection patterns in `src/credential_detector.py`
5. Add mandatory 5-second delay before approving credential-flagged actions:
   ```python
   if credential_detected:
       time.sleep(5)  # Operator has time to read warning
   ```

---

## Emergency Procedures

### Runaway HID Actions

**Symptoms**: HID executor typing uncontrollably, operator did not approve actions.

**IMMEDIATE ACTION**:
1. **Toggle kill switch to OFF**
2. **Disconnect USB cable from Pico W**
3. **Physically move target system mouse away from critical buttons**

**Post-Incident**:
1. Review session logs to understand what happened
2. Check Brain service logs for mode transition anomaly
3. File incident report with timestamp, mode, and actions executed
4. **Do not restart HID executor until root cause identified**

---

### Fire/Smoke from Hardware

**IMMEDIATE ACTION**:
1. **Toggle kill switch to OFF**
2. **Unplug all power sources** (Brain VM, Pico W, webcam)
3. **Evacuate area if smoke persists**

**Post-Incident**:
1. Inspect hardware for burnt components (capacitors, regulators, wiring)
2. **Do not power on until electrically inspected by qualified personnel**
3. File safety incident report

---

**See also**:
- [Test Plans](08_TEST_PLANS.md)
- [Setup Guides](05_SETUP_BRAIN_VM.md)
- [Threat Model](10_THREAT_MODEL.md)
