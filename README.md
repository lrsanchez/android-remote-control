# Android Tablet Control

Small KDE-friendly toolkit to control an Android tablet from Linux using:

- `scrcpy`
- a tray launcher
- a small helper portal window
- optional KWin edge-trigger integration
- wireless ADB over Tailscale

This project is built around a practical constraint: fully invisible/headless
control was not reliable on this device, so the current working setup uses a
small focusable helper window near the panel/tray.

Host platform notes:

- Linux/KDE Plasma: fully supported by this repo
- Windows: partial support documented in `WINDOWS.md`

## What Works

- Start tablet control from KDE without opening a terminal
- Control the tablet over USB or wireless ADB
- Use Tailscale for cable-free control
- Keep a small helper portal window near the bottom-right corner
- Activate/deactivate through a tray icon
- Optional KWin script for edge-triggered activation

## Windows Hosts

Windows host machines can use the same Android/Tailscale/ADB idea, but the
current Linux-specific integrations do not carry over directly.

See:

- `WINDOWS.md`

Summary:

- `scrcpy` control works on Windows
- Tailscale + wireless ADB works on Windows
- KDE tray/KWin edge integration from this repo does not apply on Windows
- a separate Windows tray app would be needed for a native equivalent

## Current Architecture

- `tray.py`
  - system tray app
  - starts/restarts the control manager
  - activates/deactivates tablet mode
- `client.py`
  - D-Bus manager process
  - launches/stops `scrcpy`
- `run-scrcpy-hid.sh`
  - main working path
  - uses `scrcpy` HID/UHID mode
  - targets the tablet over ADB/Tailscale
- `run-scrcpy-otg.sh`
  - USB OTG fallback
- `kde/kwin-remote-input`
  - KWin script for edge/shortcut integration

## Requirements

- Linux desktop with KDE Plasma
- ADB available in `PATH`
- Tailscale configured on both devices if using wireless mode
- Android tablet with developer options and USB debugging enabled
- Python 3 with:
  - `dbus`
  - `gi`
  - `Gtk`
  - `AppIndicator3`

## scrcpy

This repo includes a local `scrcpy` binary under:

`tools/scrcpy-linux-x86_64-v4.1/`

## Wireless ADB Setup

First enable TCP ADB once over USB:

```bash
adb tcpip 5555
adb connect 100.93.33.125:5555
```

Check that the tablet is reachable:

```bash
adb devices -l
```

Expected device entry:

```text
100.93.33.125:5555     device
```

## KDE Launcher

A desktop launcher is installed to:

`~/.local/share/applications/tablet-control-tray.desktop`

Search in KDE for:

`Tablet Control Tray`

You can pin it to the panel or app launcher favorites.

## Manual Start

If needed, you can run the tray manually:

```bash
python3 /var/home/leandro/Documents/dev/personal/android-remote-control/tray.py
```

Or use the helper script:

```bash
/var/home/leandro/Documents/dev/personal/android-remote-control/run-tray.sh
```

## Help Page

The tray menu includes a `Help` action which opens `HELP.md`.

It documents:

- daily use
- reboot recovery
- how to add a new tablet
- how to switch between multiple tablets
- recovery steps when activation fails

## Manual Manager Control

Start the manager directly:

```bash
env ANDROID_SERIAL=100.93.33.125:5555 \
python3 /var/home/leandro/Documents/dev/personal/android-remote-control/client.py --mode hid
```

Activate tablet mode:

```bash
qdbus org.opencode.RemoteInput /RemoteInput org.opencode.RemoteInput.ActivateTablet
```

Deactivate tablet mode:

```bash
qdbus org.opencode.RemoteInput /RemoteInput org.opencode.RemoteInput.DeactivateTablet
```

Check status:

```bash
qdbus org.opencode.RemoteInput /RemoteInput org.opencode.RemoteInput.TabletActive
```

## Adding Another Tablet

For each new tablet:

1. enable Developer Options
2. enable `USB debugging`
3. connect once by USB
4. run:

```bash
adb tcpip 5555
adb connect <tailscale-ip>:5555
```

5. in the tray:
   - `Refresh Devices`
   - `Select Device`
   - choose the new tablet

## Reboot Recovery

After reboot, wireless ADB may need reconnection:

```bash
adb connect <tailscale-ip>:5555
```

Then:

1. `Refresh Devices`
2. re-select the tablet if needed
3. `Activate Tablet`

## KWin Script

Install or refresh the KWin helper script:

```bash
./install-kwin-script.sh
```

Then enable it in KDE if needed:

- System Settings
- Window Management
- KWin Scripts

The script currently:

- registers activation hooks/shortcuts
- repositions the `Tablet Portal` window near the panel/tray
- focuses the portal when it appears

## Helper Window Behavior

The current working mode uses a small helper window because `scrcpy` needs a
real focusable window to receive mouse/keyboard input reliably.

This means:

- the helper is intentionally visible
- it is small and placed near the panel/tray
- fully hidden control was tested and rejected as unreliable on this tablet

## Files

```text
client.py                D-Bus manager for tablet mode
tray.py                  KDE tray app
run-tray.sh              starts tray if not already running
run-scrcpy-hid.sh        main wireless/ADB control path
run-scrcpy-otg.sh        USB OTG fallback path
install-kwin-script.sh   installs KWin integration
kde/                     KWin script files
icons/                   custom launcher/tray icon
desktop/                 KDE desktop launcher file
tools/                   bundled scrcpy build
```

## Notes

- No session autostart is configured by default
- Launch manually when needed
- OTG mode is retained as a fallback, but HID mode over Tailscale is the main path

## Known Limitations

- The portal window cannot be fully hidden without losing reliable input focus
- Edge-handoff is possible, but the tray workflow is currently the cleanest way to use it
- Huawei-specific behavior forced a move away from the earlier custom Android app approach
