# Run the end-to-end offline demo (all six skills, deterministic, no API key).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
.\.venv\Scripts\python.exe scripts\demo_offline.py
