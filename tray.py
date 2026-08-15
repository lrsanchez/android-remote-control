#!/usr/bin/env python3

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


class TrayApp:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.manager_process = None

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

        activate_item = Gtk.MenuItem(label="Activate Tablet")
        activate_item.connect("activate", self.on_activate)
        menu.append(activate_item)

        deactivate_item = Gtk.MenuItem(label="Deactivate Tablet")
        deactivate_item.connect("activate", self.on_deactivate)
        menu.append(deactivate_item)

        restart_item = Gtk.MenuItem(label="Restart Manager")
        restart_item.connect("activate", self.on_restart_manager)
        menu.append(restart_item)

        quit_item = Gtk.MenuItem(label="Quit Tray")
        quit_item.connect("activate", self.on_quit)
        menu.append(quit_item)

        menu.show_all()
        self.indicator.set_menu(menu)

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
                ["env", f"ANDROID_SERIAL={DEFAULT_SERIAL}", *MANAGER_CMD],
                stdout=log_file,
                stderr=log_file,
                start_new_session=True,
            )

    def refresh_status(self):
        proxy = self.manager_proxy()
        if proxy is None:
            self.status_item.set_label("Status: manager offline")
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
        self.ensure_manager()
        self.refresh_status()

    def on_quit(self, _item):
        Gtk.main_quit()


if __name__ == "__main__":
    TrayApp()
    Gtk.main()
