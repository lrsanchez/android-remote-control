#!/usr/bin/env python3
"""KDE handoff backend for Android tablet control via scrcpy.

This process exposes a small D-Bus API used by the KWin left-edge script.
`ActivateTablet` starts scrcpy in control-only mode, which then captures the
mouse/keyboard for the Android tablet. `DeactivateTablet` stops that process.
"""

import argparse
import logging
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GLib
except ImportError as exc:
    print(f"Missing runtime dependency: {exc}", file=sys.stderr)
    sys.exit(1)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("tablet-manager")

DBUS_NAME = "org.opencode.RemoteInput"
DBUS_PATH = "/RemoteInput"
DBUS_INTERFACE = "org.opencode.RemoteInput"


class ScrcpyManager:
    def __init__(self, command: list[str]):
        self.command = command
        self.process: subprocess.Popen | None = None
        self.lock = threading.Lock()

    def active(self) -> bool:
        with self.lock:
            return self.process is not None and self.process.poll() is None

    def activate(self) -> bool:
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                log.info("scrcpy already active")
                return False

            log.info("Starting tablet mode: %s", " ".join(self.command))
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True

    def deactivate(self) -> bool:
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                self.process = None
                return False

            proc = self.process
            self.process = None

        log.info("Stopping tablet mode")
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=3)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
        return True


class RemoteInputService(dbus.service.Object):
    def __init__(self, bus, manager: ScrcpyManager):
        self.manager = manager
        bus_name = dbus.service.BusName(
            DBUS_NAME,
            bus=bus,
            allow_replacement=True,
            replace_existing=True,
        )
        super().__init__(bus_name, DBUS_PATH)

    @dbus.service.method(DBUS_INTERFACE, out_signature="b")
    def ActivateTablet(self):
        return self.manager.activate()

    @dbus.service.method(DBUS_INTERFACE, out_signature="b")
    def DeactivateTablet(self):
        return self.manager.deactivate()

    @dbus.service.method(DBUS_INTERFACE, out_signature="b")
    def TabletActive(self):
        return self.manager.active()


def build_command(mode: str, serial: str | None) -> list[str]:
    root = Path(__file__).resolve().parent
    if mode == "otg":
        script = root / "run-scrcpy-otg.sh"
    else:
        script = root / "run-scrcpy-hid.sh"

    command = [str(script)]
    if serial:
        env_serial = serial
        command = ["env", f"ANDROID_SERIAL={env_serial}", str(script)]
    return command


def main():
    parser = argparse.ArgumentParser(description="Tablet mode manager backed by scrcpy")
    parser.add_argument("--mode", choices=["otg", "hid"], default="hid")
    parser.add_argument("--serial", default=os.environ.get("ANDROID_SERIAL"))
    args = parser.parse_args()

    command = build_command(args.mode, args.serial)
    manager = ScrcpyManager(command)

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    RemoteInputService(bus, manager)

    log.info("Tablet manager ready. Mode=%s", args.mode)
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
