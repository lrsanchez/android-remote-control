#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path

import dbus
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import AppIndicator3, GLib, Gtk


DBUS_NAME = "org.opencode.RemoteInput"
DBUS_PATH = "/RemoteInput"
DBUS_INTERFACE = "org.opencode.RemoteInput"
ROOT = Path(__file__).resolve().parent
MANAGER_CMD = ["python3", str(ROOT / "client.py"), "--mode", "hid"]
LOG_FILE = "/tmp/tablet-manager-hid.log"
DEFAULT_SERIAL = "100.93.33.125:5555"
ICON_NAME = "tablet-control-tray"
HELP_FILE = ROOT / "HELP.md"


class TrayApp:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.manager_process = None
        self.selected_serial = os.environ.get("ANDROID_SERIAL", DEFAULT_SERIAL)
        self.device_items = []

        self.indicator = AppIndicator3.Indicator.new(
            "remote-input-tablet",
            ICON_NAME,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title("Tablet Control")

        menu = Gtk.Menu()

        self.status_item = Gtk.MenuItem(label="Status: starting")
        self.status_item.set_sensitive(False)
        menu.append(self.status_item)

        self.serial_item = Gtk.MenuItem(label=f"Device: {self.selected_serial}")
        self.serial_item.set_sensitive(False)
        menu.append(self.serial_item)

        menu.append(Gtk.SeparatorMenuItem())

        self.devices_header = Gtk.MenuItem(label="Devices")
        self.devices_header.set_sensitive(False)
        menu.append(self.devices_header)

        self.devices_menu = Gtk.Menu()
        self.devices_item = Gtk.MenuItem(label="Select Device")
        self.devices_item.set_submenu(self.devices_menu)
        menu.append(self.devices_item)

        refresh_devices_item = Gtk.MenuItem(label="Refresh Devices")
        refresh_devices_item.connect("activate", self.on_refresh_devices)
        menu.append(refresh_devices_item)

        menu.append(Gtk.SeparatorMenuItem())

        activate_item = Gtk.MenuItem(label="Activate Tablet")
        activate_item.connect("activate", self.on_activate)
        menu.append(activate_item)

        deactivate_item = Gtk.MenuItem(label="Deactivate Tablet")
        deactivate_item.connect("activate", self.on_deactivate)
        menu.append(deactivate_item)

        restart_item = Gtk.MenuItem(label="Restart Manager")
        restart_item.connect("activate", self.on_restart_manager)
        menu.append(restart_item)

        help_item = Gtk.MenuItem(label="Help")
        help_item.connect("activate", self.open_help)
        menu.append(help_item)

        quit_item = Gtk.MenuItem(label="Quit Tray")
        quit_item.connect("activate", self.on_quit)
        menu.append(quit_item)

        menu.show_all()
        self.indicator.set_menu(menu)

        self.rebuild_devices_menu()
        self.ensure_manager()
        self.refresh_status()
        GLib.timeout_add_seconds(2, self.refresh_status)

    def manager_proxy(self):
        try:
            obj = self.bus.get_object(DBUS_NAME, DBUS_PATH)
            return dbus.Interface(obj, DBUS_INTERFACE)
        except dbus.DBusException:
            return None

    def ensure_manager(self):
        if self.manager_proxy() is not None:
            return
        with open(LOG_FILE, "a", encoding="utf-8") as log_file:
            self.manager_process = subprocess.Popen(
                ["env", f"ANDROID_SERIAL={self.selected_serial}", *MANAGER_CMD],
                stdout=log_file,
                stderr=log_file,
                start_new_session=True,
            )

    def adb_devices(self):
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.SubprocessError:
            return []

        devices = []
        for line in result.stdout.splitlines()[1:]:
            line = line.strip()
            if not line or " device" not in line:
                continue
            parts = line.split()
            serial = parts[0]
            if len(parts) == 1 or parts[1] != "device":
                continue
            label = serial
            model = None
            for part in parts[2:]:
                if part.startswith("model:"):
                    model = part.removeprefix("model:").replace("_", " ")
            if ":" in serial:
                connection = "Tailscale/ADB" if serial.startswith("100.") else "TCP/ADB"
            else:
                connection = "USB"
            if model:
                label = f"{model} ({connection})"
            else:
                label = f"{serial} ({connection})"
            devices.append((serial, label))
        return devices

    def rebuild_devices_menu(self):
        for child in self.devices_menu.get_children():
            self.devices_menu.remove(child)

        devices = self.adb_devices()
        if not devices:
            item = Gtk.MenuItem(label="No ADB devices")
            item.set_sensitive(False)
            self.devices_menu.append(item)
            self.devices_menu.show_all()
            return

        group_head = None
        for serial, label in devices:
            item = Gtk.RadioMenuItem.new_with_label_from_widget(group_head, label)
            if group_head is None:
                group_head = item
            item.set_active(serial == self.selected_serial)
            item.connect("toggled", self.on_select_device, serial)
            self.devices_menu.append(item)

        self.devices_menu.show_all()

    def on_select_device(self, item, serial):
        if not item.get_active() or serial == self.selected_serial:
            return
        self.selected_serial = serial
        self.serial_item.set_label(f"Device: {self.selected_serial}")
        self.on_restart_manager(None)

    def on_refresh_devices(self, _item):
        self.rebuild_devices_menu()
        self.serial_item.set_label(f"Device: {self.selected_serial}")

    def refresh_status(self):
        proxy = self.manager_proxy()
        if proxy is None:
            self.status_item.set_label("Status: manager offline")
            self.serial_item.set_label(f"Device: {self.selected_serial}")
            self.indicator.set_icon_full(ICON_NAME, "Tablet manager offline")
            self.ensure_manager()
            return True

        try:
            active = bool(proxy.TabletActive())
        except dbus.DBusException:
            self.status_item.set_label("Status: manager error")
            self.indicator.set_icon_full(ICON_NAME, "Tablet manager error")
            return True

        if active:
            self.status_item.set_label("Status: tablet active")
            self.indicator.set_icon_full(ICON_NAME, "Tablet active")
        else:
            self.status_item.set_label("Status: idle")
            self.indicator.set_icon_full(ICON_NAME, "Tablet idle")
        self.serial_item.set_label(f"Device: {self.selected_serial}")
        return True

    def on_activate(self, _item):
        self.ensure_manager()
        proxy = self.manager_proxy()
        if proxy is not None:
            proxy.ActivateTablet()
        self.refresh_status()

    def on_deactivate(self, _item):
        proxy = self.manager_proxy()
        if proxy is not None:
            proxy.DeactivateTablet()
        self.refresh_status()

    def on_restart_manager(self, _item):
        subprocess.run(["pkill", "-f", str(ROOT / "client.py")], check=False)
        self.rebuild_devices_menu()
        self.ensure_manager()
        self.refresh_status()

    def open_help(self, _item):
        subprocess.Popen(["xdg-open", str(HELP_FILE)])

    def on_quit(self, _item):
        Gtk.main_quit()


if __name__ == "__main__":
    TrayApp()
    Gtk.main()
