#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog

import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as Item


ROOT = Path(__file__).resolve().parent
APP_DIR = Path(os.environ.get("APPDATA", str(ROOT))) / "TabletControlTray"
APP_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = APP_DIR / "config.json"

DEFAULTS = {
    "selected_serial": "100.93.33.125:5555",
    "scrcpy_path": str(ROOT / "tools" / "scrcpy-win64-v4.1" / "scrcpy.exe"),
    "adb_path": str(ROOT / "tools" / "platform-tools" / "adb.exe"),
}


class TabletTray:
    def __init__(self):
        self.config = self.load_config()
        self.scrcpy_process = None
        self.lock = threading.Lock()
        self.icon = pystray.Icon(
            "tablet-control-tray",
            self.build_icon(),
            "Tablet Control",
            menu=pystray.Menu(self.status_item, self.device_menu, Item("Refresh Devices", self.refresh_devices), Item("Pair Device...", self.pair_device), Item("Set Device Address...", self.set_device_address), Item("Activate Tablet", self.activate_tablet), Item("Deactivate Tablet", self.deactivate_tablet), Item("Reconnect ADB", self.reconnect_adb), Item("Quit", self.quit_app)),
        )

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                return {**DEFAULTS, **data}
            except Exception:
                pass
        self.save_config(DEFAULTS)
        return dict(DEFAULTS)

    def save_config(self, data=None):
        if data is not None:
            self.config = dict(data)
        with CONFIG_FILE.open("w", encoding="utf-8") as fh:
            json.dump(self.config, fh, indent=2)

    def build_icon(self):
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((10, 6, 54, 58), radius=9, fill=(31, 41, 55, 255))
        draw.rounded_rectangle((14, 11, 50, 50), radius=6, fill=(15, 23, 42, 255))
        draw.line((5, 28, 20, 28), fill=(248, 250, 252, 255), width=5)
        draw.line((12, 21, 5, 28), fill=(248, 250, 252, 255), width=5)
        draw.line((12, 35, 5, 28), fill=(248, 250, 252, 255), width=5)
        draw.arc((20, 18, 46, 42), start=220, end=320, fill=(125, 211, 252, 255), width=5)
        draw.polygon([(40, 16), (46, 22), (40, 28)], fill=(224, 242, 254, 255))
        draw.ellipse((30, 52, 34, 56), fill=(148, 163, 184, 255))
        return image

    def adb_devices(self):
        adb = self.config["adb_path"]
        if not Path(adb).exists():
            return []
        try:
            result = subprocess.run([adb, "devices", "-l"], capture_output=True, text=True, check=True)
        except subprocess.SubprocessError:
            return []

        devices = []
        for line in result.stdout.splitlines()[1:]:
            line = line.strip()
            if not line or " device" not in line:
                continue
            parts = line.split()
            if len(parts) < 2 or parts[1] != "device":
                continue
            serial = parts[0]
            model = None
            for part in parts[2:]:
                if part.startswith("model:"):
                    model = part.removeprefix("model:").replace("_", " ")
                    break
            if ":" in serial:
                conn = "Tailscale/ADB" if serial.startswith("100.") else "TCP/ADB"
            else:
                conn = "USB"
            label = f"{model} ({conn})" if model else f"{serial} ({conn})"
            devices.append((serial, label))
        return devices

    def is_active(self):
        with self.lock:
            return self.scrcpy_process is not None and self.scrcpy_process.poll() is None

    def current_status(self):
        return f"Status: {'tablet active' if self.is_active() else 'idle'} | Device: {self.config['selected_serial']}"

    @property
    def status_item(self):
        return Item(lambda _: self.current_status(), None, enabled=False)

    def _select_handler(self, serial):
        def handler(icon, item):
            self.select_device(serial)
        return handler

    @property
    def device_menu(self):
        def make_items():
            items = []
            for serial, label in self.adb_devices():
                items.append(Item(label, self._select_handler(serial), checked=lambda item, s=serial: self.config["selected_serial"] == s, radio=True))
            if not items:
                items.append(Item("No ADB devices", None, enabled=False))
            return items

        return Item("Select Device", pystray.Menu(lambda: make_items()))

    def select_device(self, serial):
        if self.config["selected_serial"] == serial:
            return
        self.config["selected_serial"] = serial
        self.save_config()
        self.deactivate_tablet()
        self.refresh_menu()

    def refresh_menu(self, *_args):
        self.icon.update_menu()

    def refresh_devices(self, *_args):
        self.refresh_menu()

    def activate_tablet(self, *_args):
        with self.lock:
            if self.scrcpy_process is not None and self.scrcpy_process.poll() is None:
                return

            scrcpy = self.config["scrcpy_path"]
            if not Path(scrcpy).exists():
                return
            env = os.environ.copy()
            env["ANDROID_SERIAL"] = self.config["selected_serial"]
            cmd = [
                scrcpy,
                f"--serial={self.config['selected_serial']}",
                "--no-audio",
                "--keyboard=uhid",
                "--mouse=uhid",
                "--window-title=Tablet Portal",
                "--always-on-top",
                "--window-x=1482",
                "--window-y=677",
                "--window-width=154",
                "--window-height=294",
                "--max-size=336",
            ]
            self.scrcpy_process = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.refresh_menu()

    def deactivate_tablet(self, *_args):
        with self.lock:
            if self.scrcpy_process is None:
                return
            proc = self.scrcpy_process
            self.scrcpy_process = None
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        self.refresh_menu()

    def reconnect_adb(self, *_args):
        adb = self.config["adb_path"]
        serial = self.config["selected_serial"]
        if not Path(adb).exists() or ":" not in serial:
            return
        subprocess.run([adb, "connect", serial], check=False)
        self.refresh_menu()

    def _force_foreground(self, hwnd):
        # SetForegroundWindow alone is refused by Windows unless the calling
        # thread currently "owns" user input focus, which the tray icon's
        # background message-loop thread does not. AttachThreadInput lets our
        # thread borrow that right from whichever thread currently has it.
        import ctypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        fg_hwnd = user32.GetForegroundWindow()
        fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
        cur_thread = kernel32.GetCurrentThreadId()
        attached = False
        if fg_thread and fg_thread != cur_thread:
            attached = bool(user32.AttachThreadInput(fg_thread, cur_thread, True))
        try:
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        finally:
            if attached:
                user32.AttachThreadInput(fg_thread, cur_thread, False)

    def _dialog_root(self):
        # A withdrawn root can't hand keyboard focus to its dialogs on Windows
        # (background pythonw process + hidden owner window = no focus).
        # Use an invisible-but-mapped window instead so it can be foregrounded.
        root = tk.Tk()
        root.attributes("-alpha", 0.0)
        root.attributes("-topmost", True)
        root.geometry("1x1+100+100")
        root.update_idletasks()
        root.lift()
        root.focus_force()
        try:
            self._force_foreground(root.winfo_id())
        except Exception:
            pass
        return root

    def _run_dialog(self, fn):
        # Run on a dedicated thread, not the tray icon's own message-loop
        # thread: nesting Tk's event pump inside pystray's TrackPopupMenu
        # call (which is still on the stack when a menu click fires) causes
        # keyboard input to misroute even when the dialog visibly has focus.
        result = {}

        def worker():
            result["value"] = fn()

        t = threading.Thread(target=worker)
        t.start()
        t.join()
        return result.get("value")

    def _prompt(self, title, message, initialvalue=None):
        def fn():
            root = self._dialog_root()
            try:
                return simpledialog.askstring(title, message, initialvalue=initialvalue, parent=root)
            finally:
                root.destroy()

        return self._run_dialog(fn)

    def _notify(self, title, message, is_error=False):
        def fn():
            root = self._dialog_root()
            try:
                if is_error:
                    messagebox.showerror(title, message, parent=root)
                else:
                    messagebox.showinfo(title, message, parent=root)
            finally:
                root.destroy()

        self._run_dialog(fn)

    def pair_device(self, *_args):
        pair_addr = self._prompt(
            "Pair Device",
            "Pairing address (ip:port) from the tablet's\n"
            "Wireless debugging > Pair device with pairing code screen:",
        )
        if not pair_addr:
            return
        code = self._prompt("Pair Device", "6-digit pairing code shown on the tablet:")
        if not code:
            return

        adb = self.config["adb_path"]
        result = subprocess.run(
            [adb, "pair", pair_addr.strip(), code.strip()],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode == 0 and "Successfully paired" in result.stdout:
            self._notify("Pair Device", output or "Paired successfully.")
        else:
            self._notify("Pair Device", output or "Pairing failed.", is_error=True)
        self.refresh_menu()

    def set_device_address(self, *_args):
        addr = self._prompt(
            "Set Device Address",
            "Device connect address (ip:port) from the tablet's\nWireless debugging screen:",
            initialvalue=self.config["selected_serial"],
        )
        if not addr:
            return
        addr = addr.strip()
        self.config["selected_serial"] = addr
        self.save_config()

        adb = self.config["adb_path"]
        result = subprocess.run([adb, "connect", addr], capture_output=True, text=True, check=False)
        output = (result.stdout + result.stderr).strip()
        self._notify("Set Device Address", output or f"Set to {addr}")
        self.deactivate_tablet()
        self.refresh_menu()

    def quit_app(self, *_args):
        self.deactivate_tablet()
        self.icon.stop()

    def run(self):
        self.icon.run()


if __name__ == "__main__":
    TabletTray().run()
