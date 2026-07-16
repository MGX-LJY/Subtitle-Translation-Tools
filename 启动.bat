@echo off
title SRT Subtitle Translator
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" goto novenv

echo Starting server... browser will open http://127.0.0.1:8000
echo Close this window to stop the server.
echo.

start "" /min cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"

".venv\Scripts\python.exe" -X utf8 web_app.py

echo.
echo Server stopped.
pause
exit /b 0

:novenv
echo [ERROR] .venv not found. Please run:
echo     python -m venv .venv
echo     .venv\Scripts\python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
echo     .venv\Scripts\python -m pip install -r requirements.txt
pause
exit /b 1
