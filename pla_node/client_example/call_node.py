"""Minimal client example for PLA Node.
Call /os-info and /usb-list using X-API-Key.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict

import requests

API_KEY = os.getenv("PLA_API_KEY")
BASE_URL = os.getenv("PLA_NODE_URL", "http://localhost:8787")


def call(endpoint: str) -> Dict[str, Any]:
    if not API_KEY:
        print("PLA_API_KEY is required", file=sys.stderr)
        sys.exit(1)
    url = f"{BASE_URL.rstrip('/')}{endpoint}"
    resp = requests.get(url, headers={"X-API-Key": API_KEY})
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    print("/os-info ->", call("/os-info"))
    print("/usb-list ->", call("/usb-list"))


if __name__ == "__main__":
    main()
