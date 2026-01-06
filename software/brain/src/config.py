"""Configuration helpers for PLA Brain service.

Provides a single BrainConfig dataclass that can be hydrated from env vars.
Lab mode keeps all I/O mocked and should be the default for tests.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CameraConfig:
    device: str = "/dev/video0"
    width: int = 1280
    height: int = 720
    fps: int = 15


@dataclass
class SerialConfig:
    port: str = "/dev/ttyACM0"
    baudrate: int = 115200
    timeout: float = 1.5
    max_text: int = 1024  # align with contract
    min_delay_s: float = 0.1  # 100ms aligns with contract
    allowed_keys: tuple[str, ...] = (
        "ctrl",
        "alt",
        "shift",
        "gui",
        "enter",
        "escape",
        "tab",
        "backspace",
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
    )
    status_heartbeat_s: float = 5.0


@dataclass
class BrainConfig:
    host: str = "0.0.0.0"
    port: int = 8787
    lab_mode: bool = False
    log_dir: Path = Path("/tmp/pla_brain_logs")
    session_log_path: Path = field(default_factory=lambda: Path("/tmp/pla_brain_logs/session.log"))
    camera: CameraConfig = field(default_factory=CameraConfig)
    serial: SerialConfig = field(default_factory=SerialConfig)
    ocr_lang: str = "eng"
    proposal_max_len: int = 128
    enable_camera: bool = True
    operator_token: str = "changeme"
    require_physical_arm: bool = True
    arm_gpio: int = 5

    @classmethod
    def from_env(cls) -> "BrainConfig":
        lab_mode = os.getenv("LAB_MODE", "false").lower() == "true"
        enable_camera = os.getenv("ENABLE_CAMERA", "true").lower() == "true"
        log_dir = Path(os.getenv("PLA_BRAIN_LOG_DIR", "/tmp/pla_brain_logs"))
        return cls(
            host=os.getenv("PLA_BRAIN_HOST", "0.0.0.0"),
            port=int(os.getenv("PLA_BRAIN_PORT", "8787")),
            lab_mode=lab_mode,
            log_dir=log_dir,
            session_log_path=Path(os.getenv("PLA_SESSION_LOG", str(log_dir / "session.log"))),
            camera=CameraConfig(
                device=os.getenv("PLA_CAMERA_DEVICE", "/dev/video0"),
                width=int(os.getenv("PLA_CAMERA_WIDTH", "1280")),
                height=int(os.getenv("PLA_CAMERA_HEIGHT", "720")),
                fps=int(os.getenv("PLA_CAMERA_FPS", "15")),
            ),
            serial=SerialConfig(
                port=os.getenv("PLA_SERIAL_PORT", "/dev/ttyACM0"),
                baudrate=int(os.getenv("PLA_SERIAL_BAUD", "115200")),
                timeout=float(os.getenv("PLA_SERIAL_TIMEOUT", "1.5")),
                max_text=int(os.getenv("PLA_EXEC_MAX_TEXT", "1024")),
                min_delay_s=float(os.getenv("PLA_EXEC_MIN_DELAY", "0.2")),
            ),
            ocr_lang=os.getenv("PLA_OCR_LANG", "eng"),
            proposal_max_len=int(os.getenv("PLA_PROPOSAL_MAX_LEN", "128")),
            enable_camera=enable_camera,
            operator_token=os.getenv("PLA_OPERATOR_TOKEN", "changeme"),
            require_physical_arm=os.getenv("PLA_REQUIRE_PHYSICAL_ARM", "true").lower() == "true",
            arm_gpio=int(os.getenv("PLA_ARM_GPIO", "5")),
        )


def ensure_log_dirs(cfg: BrainConfig) -> None:
    cfg.log_dir.mkdir(parents=True, exist_ok=True)
    cfg.session_log_path.parent.mkdir(parents=True, exist_ok=True)
