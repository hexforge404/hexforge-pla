# Setup Guide: Brain VM — HexForge PLA

**Target Platform**: Proxmox VE or standalone Linux VM  
**OS**: Ubuntu Server 22.04 LTS or Debian 12  
**Requirements**: 2 vCPU, 4GB RAM, 20GB disk minimum

---

## Pre-Setup Checklist

- [ ] Proxmox host accessible with admin credentials
- [ ] Ubuntu Server 22.04 ISO downloaded
- [ ] USB webcam available for passthrough (or network camera)
- [ ] Network connectivity to VM host
- [ ] SSH client for remote access

---

## Phase 1: VM Creation (Proxmox)

### Create VM

```bash
# Via Proxmox Web UI or CLI
qm create 200 \
  --name hexforge-pla-brain \
  --memory 4096 \
  --cores 2 \
  --net0 virtio,bridge=vmbr0 \
  --scsihw virtio-scsi-pci \
  --scsi0 local-lvm:20 \
  --ide2 local:iso/ubuntu-22.04-server-amd64.iso,media=cdrom \
  --boot order=scsi0;ide2 \
  --ostype l26 \
  --agent enabled=1
```

### USB Passthrough (Webcam)

```bash
# Find USB device
lsusb | grep -i camera

# Add to VM config
qm set 200 --usb0 host=046d:0825
```

---

## Phase 2: Base System Configuration

### Initial Update

```bash
ssh plabrain@<VM_IP>
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential git curl vim htop usbutils v4l-utils
```

### Verify USB Webcam Detection

```bash
lsusb | grep -i camera
ls -l /dev/video*
v4l2-ctl --list-devices
```

---

## Phase 3: Python Environment Setup

### Install Python 3.11+

```bash
python3 --version
# If < 3.11:
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### Create Project Directory

```bash
mkdir -p ~/hexforge-pla
cd ~/hexforge-pla
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

---

## Phase 4: AI Model Setup (Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull model
ollama pull llama2:7b-chat

# Test
ollama run llama2:7b-chat "Hello, this is a test."
```

---

## Phase 5: Configuration

Create configuration file:

```bash
mkdir -p ~/hexforge-pla/config
cat > ~/hexforge-pla/config/brain_config.yaml << 'EOF'
system:
  mode: "observe"
  log_level: "INFO"
  session_log_dir: "/var/log/hexforge-pla/sessions"

camera:
  device: "/dev/video0"
  resolution: [1920, 1080]
  fps: 30

vision:
  ocr_engine: "tesseract"
  ocr_language: "eng"
  frame_analysis_interval: 2

ai:
  backend: "ollama"
  model: "llama2:7b-chat"
  api_endpoint: "http://localhost:11434"

hid_executor:
  enabled: true
  connection_type: "serial"
  device: "/dev/ttyACM0"
  baud_rate: 115200

safety:
  max_action_length: 1024
  rate_limit_ms: 100
  require_approval: true
  session_logging: true
EOF
```

---

**See also**:
- [Architecture](01_ARCHITECTURE.md)
- [Hardware BOM](04_HARDWARE_BOM.md)
- [Setup HID Executor](07_SETUP_HID_EXECUTOR.md)
