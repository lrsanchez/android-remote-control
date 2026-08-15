@echo off
set SCRIPT_DIR=%~dp0
start "Tablet Control Tray" pythonw "%SCRIPT_DIR%tray_app.py"
