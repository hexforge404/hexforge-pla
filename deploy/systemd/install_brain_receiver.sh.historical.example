#!/usr/bin/env bash
set -euo pipefail

SERVICE_SRC="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}" )" && pwd)/brain-receiver.service"
SERVICE_DST="/etc/systemd/system/brain-receiver.service"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

install -m 0644 "$SERVICE_SRC" "$SERVICE_DST"
systemctl daemon-reload
systemctl enable brain-receiver
systemctl restart brain-receiver

echo "--- systemctl status brain-receiver ---"
systemctl status --no-pager brain-receiver || true

echo "--- listening ports 8787/8788 ---"
ss -ltnp | grep -E ':(8787|8788)\\b' || true
