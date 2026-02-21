# Fulmine-Sparks API Client - Windows PowerShell Script
# Run this script to launch the interactive client

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if requests is installed
try {
    python -c "import requests" 2>&1 | Out-Null
} catch {
    Write-Host "Installing required dependencies..." -ForegroundColor Yellow
    python -m pip install requests
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ ERROR: Failed to install requests library" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Run the client
Write-Host ""
Write-Host "Starting Fulmine-Sparks API Client..." -ForegroundColor Cyan
Write-Host ""
python client.py
