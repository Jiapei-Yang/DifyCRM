$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  python -m venv .venv
  $python = Join-Path $root ".venv\Scripts\python.exe"
}

& $python -m pip install -r (Join-Path $root "requirements.txt")
& $python (Join-Path $root "scripts\init_db.py") --reset
