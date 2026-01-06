tesseract --version
tesseract /tmp/test_frame.jpg /tmp/test_output
dmesg | grep -i video
# Setup Guide: Raspberry Pi CSI Camera — HexForge PLA

**Goal:** Attach and verify the CSI ribbon camera used by the PLA Brain for capture/OCR. Safety and contracts remain unchanged: Brain only observes; Hands execute.

**Hardware Baseline**
- Raspberry Pi (model-agnostic) with CSI connector.
- Official-style CSI camera module (e.g., V2 or HQ) with flat flex ribbon.
- No USB webcams in this path; CSI is required for deterministic capture.

---

## Physical Attachment

### Ribbon Orientation
```
Pi CSI Connector (hinge lifts)       Camera PCB
┌───────────────┐                    ┌─────────┐
│ [========]    │  <--- contacts     │  Lens   │
│               │                    │         │
└───────────────┘                    └─────────┘
```
- Lift the black latch on the Pi CSI connector.
- Insert ribbon with **contacts facing the Pi contacts** (usually toward the HDMI port on modern Pi boards). On the camera PCB, contacts face the connector pads.
- Fully seat ribbon; close latch evenly. Tug gently to confirm retention.

### Strain Relief & Routing
- Avoid tight bends; minimum 5 mm bend radius.
- Keep ribbon clear of heatsinks and sharp edges; add Kapton tape if crossing metal.
- Do not twist the ribbon; flip at connector if you need contact orientation.

---

## Enable Camera Stack
On Raspberry Pi OS (Bullseye+):
1. Update packages: `sudo apt update && sudo apt install -y libcamera-tools v4l-utils`
2. Reboot after installation to ensure camera drivers load.
3. Verify device nodes:
    ```bash
    ls /dev/video*   # expect /dev/video0 from libcamera-vid bridge
    ```

---

## Bring-Up & Verification
1. **Detect**: `libcamera-hello -n -t 2000` (should show preview or report sensor info).
2. **Still capture**:
    ```bash
    libcamera-still -o /tmp/pla_cam_test.jpg -n --width 1280 --height 720
    ls -lh /tmp/pla_cam_test.jpg
    ```
3. **Video sanity**: `libcamera-vid -t 5000 -o /tmp/pla_cam_test.h264 -n --width 1280 --height 720`
4. **Permissions**: ensure user in `video` group: `sudo usermod -a -G video $USER` (relog).

Expected: preview opens or file sizes are non-zero; no `No cameras available` errors.

---

## Operational Guidance
- Mount camera facing the target display; avoid glare and direct sunlight.
- Prefer 1280x720 or 1920x1080 for OCR; higher resolutions increase CPU load.
- If autofocus module is used, lock focus where possible to prevent hunting. For fixed-focus, set distance once and secure.
- Power and stability: camera is powered from Pi; ensure Pi PSU is 5 V / ≥3 A.

---

## Troubleshooting
- `No cameras available`: re-seat ribbon, check latch orientation, confirm libcamera packages installed, reboot.
- Blank captures: check lens cap, focus, and lighting; verify `/dev/video0` exists.
- Intermittent detection: ribbon strain or poor seating; redo with latch fully open/closed.
- Permissions: add user to `video` group and re-login.

---

## Safety Notes
- Camera is observational only; no actuators are driven from CSI path.
- Keep ribbon and camera isolated from high-current wiring (kill switch, LED) to avoid EMI.
- Do not reroute HID through camera; Brain remains "Smart" and Hands remain on ESP32 HID executor.

---

## Quick Commands
- Preview: `libcamera-hello -n -t 2000`
- Still: `libcamera-still -o /tmp/pla_cam_test.jpg -n --width 1280 --height 720`
- Video: `libcamera-vid -t 5000 -o /tmp/pla_cam_test.h264 -n --width 1280 --height 720`

**See also**: [Architecture: Vision System](01_ARCHITECTURE.md#vision-system), [Test Plans: Camera Tests](08_TEST_PLANS.md#phase-1-component-tests).
