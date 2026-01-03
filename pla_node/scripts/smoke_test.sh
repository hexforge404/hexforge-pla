#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${PLA_NODE_URL:-http://localhost:8787}
API_KEY=${PLA_API_KEY:-}

if [[ -z "$API_KEY" ]]; then
  echo "PLA_API_KEY must be set in the environment" >&2
  exit 1
fi

# Health (no auth)
health=$(curl -sSf "$BASE_URL/health")
if ! echo "$health" | grep -q '"ok"'; then
  echo "health check failed: $health" >&2
  exit 1
fi

eos_info=$(curl -sSf -H "X-API-Key: $API_KEY" "$BASE_URL/os-info")
if ! echo "$os_info" | grep -q 'hostname'; then
  echo "os-info missing hostname: $os_info" >&2
  exit 1
fi

echo "Smoke test passed"
