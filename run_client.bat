@echo off
REM Fulmine-Sparks API Client Runner
REM This script runs the Python client with the Fulmine-Sparks API

echo.
echo ================================================================================
echo  Fulmine-Sparks API Client
echo ================================================================================
echo.

REM Check if ALBY_API_TOKEN is set
if "%ALBY_API_TOKEN%"=="" (
    echo ⚠️  ALBY_API_TOKEN is not set
    echo.
    set /p ALBY_API_TOKEN="Enter your ALBY_API_TOKEN (get from https://getalby.com - Settings - API): "
    if "%ALBY_API_TOKEN%"=="" (
        echo ❌ ALBY_API_TOKEN is required for payment detection!
        pause
        exit /b 1
    )
) else (
    echo ✅ ALBY_API_TOKEN found in environment
    echo    Token: %ALBY_API_TOKEN:~0,10%...%ALBY_API_TOKEN:~-4%
)

echo.
if not "%ALBY_NWC_URL%"=="" (
    echo ✅ ALBY_NWC_URL found in environment
) else (
    echo ℹ️  ALBY_NWC_URL not set (optional - for invoice creation via NWC)
)

echo.
echo ================================================================================
echo.

REM Set the environment variables for Python
setlocal enabledelayedexpansion

python client.py %*
if errorlevel 1 (
    echo.
    echo ❌ Error running client
    echo.
    echo Make sure you have:
    echo   - Python 3 installed
    echo   - Dependencies installed: pip install requests qrcode[pil]
    echo   - ALBY_API_TOKEN set correctly
    echo.
    pause
)
