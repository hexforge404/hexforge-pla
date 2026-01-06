"""Mode state machine for the PLA Brain."""

from __future__ import annotations

from dataclasses import dataclass

VALID_MODES = ("OBSERVE", "SUGGEST", "EXECUTE")


@dataclass
class ModeManager:
    current: str = "OBSERVE"

    def set_mode(self, mode: str) -> None:
        if mode not in VALID_MODES:
            raise ValueError(f"invalid mode: {mode}")
        self.current = mode

    def require_execute(self) -> None:
        if self.current != "EXECUTE":
            raise PermissionError("not in EXECUTE mode")

    @property
    def can_propose(self) -> bool:
        return self.current in {"SUGGEST", "EXECUTE"}

    @property
    def can_execute(self) -> bool:
        return self.current == "EXECUTE"
