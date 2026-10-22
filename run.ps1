Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "             KNOT ECOSYSTEM POWERSHELL LAUNCHER             " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Navigate to script location
Set-Location -Path $PSScriptRoot

# 2. Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python is not installed or not in PATH!" -ForegroundColor Red
    pause
    exit 1
}

# 3. Setup Virtual Environment
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[1/3] Creating virtual environment (venv)..." -ForegroundColor Yellow
    python -m venv venv
}

# 4. Install dependencies
Write-Host "[2/3] Installing / Updating requirements..." -ForegroundColor Yellow
& "venv\Scripts\python.exe" -m pip install -r backend\requirements.txt

# 5. Launch via run.py inside venv
Write-Host "[3/3] Launching Knot..." -ForegroundColor Green
& "venv\Scripts\python.exe" run.py
