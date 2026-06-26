#!/usr/bin/env bash
# Run the offline test suite (no API key required).
set -euo pipefail
cd "$(dirname "$0")/.."
./.venv/bin/python -m pytest tests -q
