"""Camera capture abstraction with LAB_MODE fallback.

In lab mode we synthesize an image with predictable text for deterministic tests.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:  # OpenCV is optional in lab mode
    import cv2  # type: ignore
except Exception:  # pragma: no cover - gracefully degrade
    cv2 = None

from config import BrainConfig


@dataclass
class Frame:
    data: np.ndarray

    def to_jpeg_bytes(self) -> bytes:
        success, buf = None, None
        if cv2 is not None:
            success, buf = cv2.imencode(".jpg", self.data)
            if success:
                return buf.tobytes()
        # Fallback with PIL to ensure tests pass without OpenCV encoders
        image = Image.fromarray(self.data)
        out = io.BytesIO()
        image.save(out, format="JPEG")
        return out.getvalue()


class CameraCapture:
    def __init__(self, cfg: BrainConfig):
        self.cfg = cfg
        self._capture = None
        if not cfg.lab_mode and cfg.enable_camera and cv2 is not None:
            self._capture = cv2.VideoCapture(cfg.camera.device)
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.camera.width)
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.camera.height)
            self._capture.set(cv2.CAP_PROP_FPS, cfg.camera.fps)

    def capture(self) -> Frame:
        if self.cfg.lab_mode or self._capture is None:
            return Frame(data=self._synthetic_frame())
        ret, frame = self._capture.read()
        if not ret:
            return Frame(data=self._synthetic_frame(text="capture_failed"))
        return Frame(data=frame)

    def _synthetic_frame(self, text: str = "PLA LAB MODE") -> np.ndarray:
        width, height = self.cfg.camera.width, self.cfg.camera.height
        image = Image.new("RGB", (width, height), color=(10, 10, 10))
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        draw.text((20, 20), text, fill=(200, 200, 200), font=font)
        return np.array(image)

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
