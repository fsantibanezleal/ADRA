#!/usr/bin/env bash
# Run the end-to-end offline demo (all six skills, deterministic, no API key).
set -euo pipefail
cd "$(dirname "$0")/.."
./.venv/bin/python scripts/demo_offline.py
