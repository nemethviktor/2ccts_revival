@echo off
rem Creates/updates the project venv (.venv in repo root) and installs tools\requirements.txt
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
    echo Creating .venv ...
    python -m venv .venv || exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r tools\requirements.txt || exit /b 1
