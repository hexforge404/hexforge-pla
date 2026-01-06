"""ASGI entrypoint for the PLA Brain FastAPI app."""

from __future__ import annotations

import uvicorn

from config import BrainConfig
from web_ui.app import build_app


cfg = BrainConfig.from_env()
app = build_app(cfg)


def main() -> None:
    uvicorn.run(app, host=cfg.host, port=cfg.port, log_level="info")


if __name__ == "__main__":
    main()
