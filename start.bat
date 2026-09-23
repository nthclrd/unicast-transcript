@echo off
REM Double-clic : lance l interface web.
cd /d "%~dp0"
uv run python server.py
pause
