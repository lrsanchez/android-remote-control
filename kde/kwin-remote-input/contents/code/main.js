var registeredBorders = [];

function placeTabletPortal(window) {
    if (!window || window.caption !== "Tablet Portal") {
        return;
    }

    var area = workspace.clientArea(KWin.FullArea, window);
    var width = Math.min(154, Math.floor(area.width * 0.11));
    var height = Math.min(294, Math.max(220, Math.floor(area.height * 0.26)));
    window.frameGeometry = {
        x: area.x + area.width - width - 12,
        y: area.y + area.height - height - 12,
        width: width,
        height: height
    };
    workspace.activeWindow = window;
}

function activateTabletMode() {
    print("kwin-remote-input: activating tablet mode");
    callDBus(
        "org.opencode.RemoteInput",
        "/RemoteInput",
        "org.opencode.RemoteInput",
        "ActivateTablet",
        function(result) {
            print("kwin-remote-input: activate result", result);
        }
    );
}

function deactivateTabletMode() {
    callDBus(
        "org.opencode.RemoteInput",
        "/RemoteInput",
        "org.opencode.RemoteInput",
        "DeactivateTablet",
        function(result) {
            print("kwin-remote-input: deactivate result", result);
        }
    );
}

function init() {
    for (var i in registeredBorders) {
        unregisterScreenEdge(registeredBorders[i]);
    }
    registeredBorders = [];

    var borders = readConfig("BorderActivate", "0").toString().split(",");
    for (var i in borders) {
        var border = parseInt(borders[i]);
        if (isFinite(border)) {
            registeredBorders.push(border);
            registerScreenEdge(border, activateTabletMode);
        }
    }
}

registerShortcut(
    "RemoteInputActivateTablet",
    "Activate Android tablet mode",
    "Meta+F12",
    activateTabletMode
);

registerShortcut(
    "RemoteInputDeactivateTablet",
    "Deactivate Android tablet mode",
    "Meta+Shift+F12",
    deactivateTabletMode
);

options.configChanged.connect(init);
workspace.windowAdded.connect(placeTabletPortal);
workspace.windowList().forEach(placeTabletPortal);
init();
