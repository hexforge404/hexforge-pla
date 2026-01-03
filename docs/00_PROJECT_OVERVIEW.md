# HexForge Lab Assistant – Portable AI Lab Node

## Purpose
This project is a PRIVATE, INTERNAL lab tool designed to assist with hardware troubleshooting, diagnostics, and controlled system interaction inside a personal workshop environment.

This device is NOT intended for sale, distribution, or unauthorized access to third-party systems.

## High-Level Concept
A portable Raspberry Pi–based AI lab node with:
- Visual input (camera)
- Physical controls (buttons)
- Status display (OLED / eInk)
- Optional RFID-based identification for inventory and workflow tagging
- Controlled HID interaction ONLY with user confirmation

The system operates as a human-in-the-loop assistant.

## Core Principles
- Human confirmation required for any action
- No autonomous keystroke injection
- No persistence across external systems
- All actions observable and interruptible

## Hardware (Current Inventory)
- Raspberry Pi 4 (primary brain)
- Raspberry Pi Zero 2 W (secondary / display node)
- Raspberry Pi Pico 2 (GPIO / button controller)
- ESP32 dev board (optional wireless coprocessor)
- Raspberry Pi Camera v2.1
- OLED displays (I2C)
- Button board (GPIO)
- RC522 RFID module (SPI)
- Battery packs / power modules (non-critical)

## Functional Roles
- Pi 4: AI host, UI, vision processing, VM access
- Pico 2: Deterministic input handling (buttons)
- OLED: Status + confirmation prompts
- RFID: Inventory & operator identification (non-secure use)
- Camera: Screen capture and visual context

## Explicit Non-Goals
- No bypassing authentication
- No cloning of secure RFID credentials
- No unattended HID actions
- No offensive or stealth usage

## Development Style
- Modular services
- Clear hardware abstraction
- Test-first bring-up
- Documentation before expansion
