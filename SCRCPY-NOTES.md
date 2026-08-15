# scrcpy pivot

Preferred control paths for this tablet:

1. `./run-scrcpy-hid.sh`
   - USB debugging path
   - small left-side helper window
   - no audio playback
   - uses UHID keyboard/mouse
   - best candidate for extended-monitor style handoff and later wireless ADB use

2. `./run-scrcpy-otg.sh`
   - USB only
   - no mirroring
   - physical mouse/keyboard over AOA
   - useful fallback if HID is unsupported on the device

Notes:
- Stop the old `Remote Input` app and disable its accessibility service.
- `scrcpy` owns the mouse capture in HID modes.
- Use the scrcpy modifier key (`Alt` or `Super`) to toggle mouse capture.
