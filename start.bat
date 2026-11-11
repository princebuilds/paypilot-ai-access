@echo off
title PayPilot AI ACCESS Server
cd /d "%~dp0"
echo =======================================================
echo Starting PayPilot AI ACCESS on http://127.0.0.1:8000
echo =======================================================
start "" "http://127.0.0.1:8000"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
) else (
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
)
pause
