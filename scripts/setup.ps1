# Create the local venv and install ADRA (editable) with dev deps. Offline-ready.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Write-Host "ADRA ready (offline, no key needed). Run: .\scripts\test.ps1  or  .\scripts\demo.ps1"
