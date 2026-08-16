# Tablet Control Help

## Daily Use

1. Start `Tablet Control Tray`
2. Open the tray icon
3. Click `Refresh Devices`
4. In `Select Device`, choose the tablet you want
5. Click `Activate Tablet`

To stop control:

1. Open the tray icon
2. Click `Deactivate Tablet`

## After Reboot

Wireless ADB often needs to be reconnected after the host or tablet reboots.

Recovery steps:

```bash
adb connect <tailscale-ip>:5555
```

Then in the tray:

1. `Refresh Devices`
2. select the `Tailscale/ADB` device
3. `Activate Tablet`

Example:

```bash
adb connect 100.93.33.125:5555
```

## New Tablet Setup

For a brand new tablet:

1. Enable Developer Options
2. Enable `USB debugging`
3. Connect the tablet once by USB
4. Authorize the host on the tablet if prompted
5. Enable ADB TCP mode:

```bash
adb tcpip 5555
```

6. Find the tablet's Tailscale IP
7. Connect over Tailscale:

```bash
adb connect <tailscale-ip>:5555
```

8. In the tray:
   - `Refresh Devices`
   - `Select Device`
   - choose the new tablet
   - `Activate Tablet`

## Multiple Tablets

If you have more than one tablet:

1. Make sure each one appears in:

```bash
adb devices -l
```

2. Open tray
3. `Refresh Devices`
4. `Select Device`
5. Choose the model/connection you want

The tray shows labels like:

- `MRO W09 (Tailscale/ADB)`
- `Galaxy Tab S9 (USB)`

## If Activate Tablet Does Nothing

Try:

1. `Deactivate Tablet`
2. `Refresh Devices`
3. choose the correct device again
4. `Activate Tablet`

If needed, restart the tray:

```bash
pkill -f "/var/home/leandro/Documents/dev/personal/android-remote-control/client.py" || true
pkill -f "/scrcpy" || true
pkill -f "/var/home/leandro/Documents/dev/personal/android-remote-control/tray.py" || true
nohup python3 "/var/home/leandro/Documents/dev/personal/android-remote-control/tray.py" >/tmp/tablet-tray.log 2>&1 &
```
