# Setup Guide: Camera & Vision — HexForge PLA

**Goal**: Configure USB webcam for screen capture and OCR  
**Estimated Time**: 30 minutes

---

## Hardware Options

### Recommended Camera: Logitech C920 HD Pro

- **Resolution**: 1080p @ 30fps
- **Focus**: Autofocus with manual override
- **Field of View**: 78° diagonal
- **Connection**: USB 2.0/3.0
- **Cost**: ~$60-80

### Alternative Cameras

- Logitech C922 Pro (similar to C920, $80-100)
- Microsoft LifeCam HD-3000 (720p budget option, $30-40)
- Generic 1080p USB camera (variable quality, $20-50)

---

## Physical Setup

### Positioning for Desktop/Laptop Screen Capture

```
┌──────────────────────────────────┐
│     Target Monitor (24")         │
│                                  │
│                                  │
└──────────────────────────────────┘
              ▲
              │ Webcam mounted on
              │ adjustable arm or
              │ tripod, ~12-18" away
              │
```

**Best Practices**:
- Mount camera 12-18 inches from screen
- Position at center of screen for minimal distortion
- Ensure no glare or reflections (disable room lights or use anti-glare screen)
- Use USB extension cable if needed (max 16ft passive, longer with active repeater)

---

## Software Configuration

### Verify Detection

```bash
# List video devices
ls -l /dev/video*

# Get camera info
v4l2-ctl --list-devices

# Show supported formats
v4l2-ctl -d /dev/video0 --list-formats-ext
```

### Set Camera Parameters

```bash
# Disable autofocus (prevents hunting)
v4l2-ctl -d /dev/video0 --set-ctrl=focus_auto=0

# Set manual focus (adjust for your distance)
v4l2-ctl -d /dev/video0 --set-ctrl=focus_absolute=10

# Adjust brightness/contrast if needed
v4l2-ctl -d /dev/video0 --set-ctrl=brightness=128
v4l2-ctl -d /dev/video0 --set-ctrl=contrast=128

# List all available controls
v4l2-ctl -d /dev/video0 --list-ctrls
```

---

## OCR Calibration

### Install Tesseract OCR

```bash
sudo apt install -y tesseract-ocr tesseract-ocr-eng
tesseract --version
```

### Test OCR with Sample Image

```bash
# Capture test frame
fswebcam -r 1920x1080 -d /dev/video0 --no-banner /tmp/test_frame.jpg

# Run OCR
tesseract /tmp/test_frame.jpg /tmp/test_output

# Review output
cat /tmp/test_output.txt
```

### Improve OCR Accuracy

1. **Focus**: Ensure text on screen is sharp
2. **Lighting**: Avoid glare and shadows
3. **Resolution**: Use 1080p minimum for small text
4. **Preprocessing**: Brightness/contrast adjustment improves results
5. **Distance**: Closer is better, but avoid distortion

---

## Integration Test

```bash
cd ~/hexforge-pla/software/brain
source venv/bin/activate
python test_camera.py
```

**Expected Output**:
```
Camera detected at /dev/video0
Resolution: 1920x1080
FPS: 30
Capturing frame... Success
OCR test: [sample text extracted from screen]
```

---

## Troubleshooting

### Camera Not Detected

```bash
# Check USB connection
lsusb | grep -i camera

# Check kernel messages
dmesg | grep -i video

# Try different USB port (prefer USB 3.0)
```

### Poor OCR Results

- Increase camera resolution to 1080p or higher
- Disable autofocus and set manual focus
- Adjust screen brightness (brighter helps OCR)
- Ensure no glare or reflections
- Move camera closer (but keep entire screen in frame)

### Permission Issues

```bash
# Add user to video group
sudo usermod -a -G video $USER
# Log out and back in
```

---

**See also**:
- [Architecture: Vision System](01_ARCHITECTURE.md#vision-system)
- [Test Plans: Camera Tests](08_TEST_PLANS.md#phase-1-component-tests)
- [Runbooks: Camera Issues](09_RUNBOOKS.md#camera-not-detecting-screen-changes)
