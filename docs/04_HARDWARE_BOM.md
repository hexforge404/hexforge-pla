# Hardware Bill of Materials (BOM) — HexForge PLA

**Last Updated**: 2026-01-01  
**Status**: Initial planning / parts sourcing

## Required Components

### Brain (Option A: Raspberry Pi 4)

| Component | Specification | Quantity | Est. Cost | Source | Notes |
|-----------|--------------|----------|-----------|--------|-------|
| Raspberry Pi 4 | 4GB or 8GB RAM | 1 | $55-75 | Adafruit, CanaKit | Preferred for portable setup |
| MicroSD Card | 64GB+ Class 10 / A2 | 1 | $15 | Samsung EVO Select | Brain OS + storage |
| Power Supply | 5V 3A USB-C | 1 | $10 | Official RPi adapter | UL listed required |
| Case with Fan | Aluminum or plastic | 1 | $15 | Flirc, Argon ONE | Passive cooling preferred |
| Heatsinks | Aluminum | 1 set | $5 | Generic | If not included in case |

**Subtotal (RPi4 Brain)**: ~$100-120

### Brain (Option B: Proxmox VM)

| Component | Specification | Quantity | Notes |
|-----------|--------------|----------|-------|
| Proxmox Host | Existing server | 1 | Assumed available |
| VM Resources | 2 vCPU, 4GB RAM, 20GB disk | 1 | Allocate from host pool |
| USB Passthrough | Camera device passthrough | - | PCI USB controller passthrough recommended |

**Subtotal (VM Brain)**: $0 (assumes existing infrastructure)

### HID Executor (Required)

| Component | Specification | Quantity | Est. Cost | Source | Notes |
|-----------|--------------|----------|-----------|--------|-------|
| Raspberry Pi Pico W | RP2040 with WiFi | 1 | $6 | Adafruit, PiShop | WiFi optional, can use Pico (no W) |
| USB Cable | Micro-USB to USB-A, 3ft | 1 | $5 | Anker, Amazon Basics | Data + power |
| Kill Switch | SPST Toggle, 10A | 1 | $5 | DigiKey, Mouser | Inline power interrupt |
| HID Armed LED | Red LED 5mm + resistor | 1 | $2 | Generic assortment | 330Ω resistor for 3.3V |
| Enclosure | Small project box | 1 | $8 | Hammond, Adafruit | Must fit Pico + switch + LED |
| Breadboard (temp) | Half-size | 1 | $4 | Generic | For prototyping |
| Jumper Wires | Male-male assortment | 1 pack | $6 | Generic | Prototyping |

**Subtotal (HID Executor)**: ~$36

### Vision (Eyes) — Required

| Component | Specification | Quantity | Est. Cost | Source | Notes |
|-----------|--------------|----------|-----------|--------|-------|
| USB Webcam | 1080p, 30fps, autofocus | 1 | $30-60 | Logitech C920/C922 | Wide angle preferred |
| Webcam Mount | Adjustable arm or tripod | 1 | $15-25 | Generic | Must aim at target screen |
| USB Extension | USB-A 3.0, 6-10ft | 1 | $10 | Anker | Active cable if >10ft |

**Subtotal (Vision)**: ~$55-95

### Optional: E-ink Status Display

| Component | Specification | Quantity | Est. Cost | Source | Notes |
|-----------|--------------|----------|-----------|--------|-------|
| Raspberry Pi Zero 2 W | ARM Cortex-A53, WiFi | 1 | $15 | Adafruit, PiShop | Can use Zero W (slower) |
| E-ink Display | 2.13" or 2.9" SPI | 1 | $20-30 | Waveshare, Adafruit | Partial refresh capable |
| MicroSD Card | 16GB+ | 1 | $8 | SanDisk | Minimal storage needed |
| Power Supply | 5V 2A Micro-USB | 1 | $8 | Official RPi adapter | |
| Case | Zero-compatible | 1 | $8 | Adafruit, PiMoroni | Must expose GPIO for display |

**Subtotal (Status Display)**: ~$60-70

## Total Cost Summary

| Configuration | Total Cost (USD) |
|---------------|------------------|
| **Minimum Viable** (RPi4 Brain + HID + Webcam) | ~$190-250 |
| **VM Brain** (HID + Webcam, assuming existing Proxmox) | ~$90-130 |
| **Full Portable** (RPi4 + HID + Webcam + Status Display) | ~$250-320 |
| **Complete Lab Setup** (All options, RPi4 brain) | ~$400-500 |

---

**See also**:
- [Architecture](01_ARCHITECTURE.md)
- [Setup Guides](05_SETUP_BRAIN_VM.md)
- [Wiring Diagrams](07_SETUP_HID_EXECUTOR.md)
