@echo off
REM Windows: double-click to run
cd /d "%~dp0"
python bridge.py --port 8765 --workdir "%USERPROFILE%\ScienceMentor"
pause
