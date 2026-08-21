@echo off
set SCRIPT_DIR=%~dp0
where pyw >nul 2>nul
if %ERRORLEVEL%==0 (
    start "Tablet Control Tray" pyw -3 "%SCRIPT_DIR%tray_app.py"
) else (
    start "Tablet Control Tray" pythonw "%SCRIPT_DIR%tray_app.py"
)
