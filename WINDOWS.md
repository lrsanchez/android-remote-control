# Windows Host Support

This project currently targets Linux hosts, especially KDE Plasma on Wayland.

Windows hosts can still use the same core Android control path:

- `scrcpy`
- ADB over USB or wireless ADB
- Tailscale for remote connectivity

But the following parts of this repo are Linux/KDE-specific and do **not** work
as-is on Windows:

- `tray.py`
- `client.py` D-Bus integration
- KWin script integration in `kde/`
- `qdbus` activation flow
- KDE launcher/panel behavior

## What Works on Windows

On Windows, the practical support path is:

1. Install `scrcpy`
2. Install ADB / Android platform-tools
3. Enable USB debugging on the tablet
4. Optionally enable wireless ADB and connect through Tailscale
5. Run `scrcpy` directly

## Recommended Windows Workflow

### 1. Connect ADB over USB first

Enable:

- Developer options
- USB debugging

Then confirm the device is visible from a Command Prompt or PowerShell window:

```powershell
adb devices
```

### 2. Enable wireless ADB

Once connected over USB:

```powershell
adb tcpip 5555
```

### 3. Connect over Tailscale

Find the tablet's Tailscale IP, then:

```powershell
adb connect <tailscale-ip>:5555
```

Example:

```powershell
adb connect 100.93.33.125:5555
```

### 4. Start scrcpy

For a small helper window style similar to the Linux HID path:

```powershell
scrcpy --serial=<tailscale-ip>:5555 --no-audio --keyboard=uhid --mouse=uhid
```

Example:

```powershell
scrcpy --serial=100.93.33.125:5555 --no-audio --keyboard=uhid --mouse=uhid
```

## Notes About Windows

- `scrcpy` itself works well on Windows
- Tailscale + wireless ADB works the same conceptually
- HID/UHID support depends on the Android device behavior, not just the host OS
- The Linux tray UX from this repo is not implemented for Windows yet

## What Is Missing for Native Windows Support

To support Windows in a way similar to this Linux/KDE setup, a separate Windows
frontend would need to be built.

That would likely include:

- a Windows tray icon/app
- device selection UI
- start/stop manager logic
- optional edge-handoff logic using Windows APIs
- process management around `scrcpy`

## Current Recommendation

If you want to use this setup from Windows today:

- use `scrcpy` directly
- use ADB over Tailscale
- treat the Linux/KDE-specific pieces in this repo as a reference architecture,
  not a Windows-ready implementation
