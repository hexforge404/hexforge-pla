#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

: "${BRAIN_RECEIVER_PORT:=8788}"
export BRAIN_RECEIVER_PORT
export PORT="$BRAIN_RECEIVER_PORT"
export FLASK_RUN_PORT="$BRAIN_RECEIVER_PORT"
export FLASK_APP=app.py
python app.py
