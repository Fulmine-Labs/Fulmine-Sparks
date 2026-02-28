@echo off
REM Fulmine-Sparks API Client Runner
REM This script runs the Python client with the Fulmine-Sparks API

python client.py %*
if errorlevel 1 (
    echo.
    echo Error: Make sure you have Python 3 installed and requests module installed
    echo Install with: pip install requests qrcode[pil]
    pause
)
