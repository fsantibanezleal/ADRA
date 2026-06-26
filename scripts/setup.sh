#!/usr/bin/env bash
# Create the local venv and install ADRA (editable) with dev deps. Offline-ready.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e ".[dev]"
echo "ADRA ready (offline, no key needed). Run: ./scripts/test.sh  or  ./scripts/demo.sh"
