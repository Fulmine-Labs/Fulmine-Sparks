@echo off
REM Fulmine-Sparks API Client Runner
REM This script runs the Python client with the Fulmine-Sparks API

REM Set your Alby API Token here or it will prompt you
REM Get it from: https://getalby.com -> Settings -> API & Extensions
if "%ALBY_API_TOKEN%"=="" (
    set /p ALBY_API_TOKEN="Enter your ALBY_API_TOKEN (or press Enter to skip): "
)

REM Optional: Set Alby NWC URL for invoice creation
REM Get it from Alby Hub App Store
if not "%ALBY_NWC_URL%"=="" (
    echo Using ALBY_NWC_URL: %ALBY_NWC_URL:~0,30%...
)

python client.py %*
if errorlevel 1 (
    echo.
    echo Error: Make sure you have Python 3 installed and dependencies installed
    echo Install with: pip install requests qrcode[pil]
    echo.
    echo Also make sure ALBY_API_TOKEN is set for payment detection
    pause
)
