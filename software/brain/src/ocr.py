"""OCR abstraction with lab-mode fallback."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover
    pytesseract = None

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

from config import BrainConfig

logger = logging.getLogger("pla.brain.ocr")


class OCREngine:
    def __init__(self, cfg: BrainConfig):
        self.cfg = cfg

    def extract_text(self, frame: np.ndarray) -> str:
        if self.cfg.lab_mode or pytesseract is None or cv2 is None:
            return "Hello from LAB MODE"
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        try:
            text = pytesseract.image_to_string(gray, lang=self.cfg.ocr_lang)
            return text.strip()
        except Exception as exc:  # pragma: no cover
            logger.warning("OCR failed: %s", exc)
            return ""
