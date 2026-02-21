@echo off
REM Fulmine-Sparks API Client - Windows Batch Script
REM This script runs the Python client with proper error handling

setlocal enabledelayedexpansion

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Python is not installed or not in PATH
    echo ============================================================
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Check if requests library is installed
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ============================================================
    echo Installing required dependencies...
    echo ============================================================
    echo.
    python -m pip install requests
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install requests library
        echo.
        pause
        exit /b 1
    )
)

REM Run the client
python client.py %*
