# Windows Tray App

This folder contains a Windows-native tray frontend for controlling Android tablets with:

- `scrcpy`
- ADB
- Tailscale or USB

## Files

- `tray_app.py` - Windows tray application
- `run-tray.bat` - starts tray app without opening a terminal
- `install.ps1` - downloads `scrcpy` and platform-tools, installs Python deps, creates a Start Menu shortcut
- `requirements.txt` - Python dependencies

## Install

From PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

## Use

Start `Tablet Control Tray` from the Start Menu.

Tray features:

- select connected ADB device
- activate tablet mode
- deactivate tablet mode
- reconnect wireless ADB

## Notes

- Device labels show model + connection type
- Wireless devices should be connected first with:

```powershell
adb connect <tailscale-ip>:5555
```
