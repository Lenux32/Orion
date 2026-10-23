"""Sandboxed VM — Made by 2pro12342.

Run as main.py in a CodeHS Python Graphics (tkinter) sandbox.
This is a real Linux desktop session with native applications, not an OS mockup.
Packages are extracted into this program's own directory, without sudo.
Roblox is a website shortcut; a native Roblox Linux client is not included.
"""
import atexit
import json
import math
import os
from pathlib import Path
import queue
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import threading
import time
import tkinter as tk
from tkinter import messagebox
from xml.sax.saxutils import escape
from concurrent.futures import ThreadPoolExecutor

TITLE = "Sandboxed VM"
AUTHOR = "2pro12342"
# Explicitly approved by the user for Chrome inside this CodeHS Linux session.
# Set False to require Chrome's own sandbox and block unsupported launches.
ALLOW_CHROME_WITHOUT_SANDBOX = True
HERE = Path(__file__).resolve().parent
BASE = HERE / ".sandboxed-vm-linux"
RUNTIME = BASE / "runtime"
DOWNLOADS = BASE / "downloads"
DOCUMENTS = HERE / "Documents"
LOGS = BASE / "logs"
APPS = BASE / "apps"
SOCKET = BASE / "control.sock"
SCRIPT = Path(__file__).resolve()
TRASH = BASE / "trash"
for directory in (BASE, RUNTIME, DOWNLOADS, DOCUMENTS, LOGS, APPS, TRASH, BASE / "profiles", BASE / "run", BASE / "icons"):
    directory.mkdir(parents=True, exist_ok=True)


def environment():
    env = os.environ.copy()
    libdirs = [RUNTIME / "usr/lib/x86_64-linux-gnu", RUNTIME / "lib/x86_64-linux-gnu"]
    env["LD_LIBRARY_PATH"] = ":".join([str(p) for p in libdirs] + [env.get("LD_LIBRARY_PATH", "")])
    env["PATH"] = str(RUNTIME / "usr/bin") + ":" + env.get("PATH", "")
    env["XDG_DATA_DIRS"] = str(RUNTIME / "usr/share") + ":" + env.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
    env["XDG_RUNTIME_DIR"] = str(BASE / "run")
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=" + str(BASE / "run/bus")
    env["NO_AT_BRIDGE"] = "1"
    env["GTK_A11Y"] = "none"
    env["DISPLAY"] = os.environ.get("DISPLAY", ":99")
    return env


def client(action):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(3)
            connection.connect(str(SOCKET))
            connection.sendall((json.dumps({"action": action}) + "\n").encode())
            print(connection.recv(16384).decode())
        return 0
    except OSError as exc:
        print("Start Sandboxed VM first:", exc)
        return 1


def checked(command, log_name="setup.log", timeout=240, env=None):
    with (LOGS / log_name).open("ab", buffering=0) as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, env=env)
    if result.returncode:
        detail = (LOGS / log_name).read_text(errors="replace")[-2200:]
        raise RuntimeError("{} failed ({}).\n{}".format(Path(command[0]).name, result.returncode, detail))


def fetch(url, destination):
    partial = destination.with_suffix(destination.suffix + ".part")
    checked(["curl", "--location", "--fail", "--retry", "2", "--connect-timeout", "25", "--max-time", "240", "--output", str(partial), url], timeout=260)
    partial.replace(destination)


def install_desktop(report):
    marker = RUNTIME / "desktop-ready.json"
    if marker.exists() and (RUNTIME / "usr/bin/jwm").exists():
        return
    release = Path("/etc/os-release").read_text()
    if 'VERSION_ID="22.04"' not in release or os.uname().machine != "x86_64":
        raise RuntimeError("The automatic package setup supports CodeHS Ubuntu 22.04 x64. This sandbox has a different runtime.")
    apt = BASE / "apt"
    archives = apt / "archives"
    for directory in (archives / "partial", apt / "lists/partial"):
        directory.mkdir(parents=True, exist_ok=True)
    shutil.copyfile("/var/lib/dpkg/status", str(apt / "status"))
    (apt / "sources.list").write_text(
        "deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu jammy main universe\n"
        "deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu jammy-updates main universe\n"
        "deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://security.ubuntu.com/ubuntu jammy-security main universe\n")
    options = []
    for key, value in {
        "Dir::State::status": apt / "status",
        "Dir::State::extended_states": apt / "extended_states",
        "Dir::State::lists": apt / "lists",
        "Dir::Cache::archives": archives,
        "Dir::Cache::pkgcache": apt / "pkgcache.bin",
        "Dir::Cache::srcpkgcache": apt / "srcpkgcache.bin",
        "Dir::Etc::sourcelist": apt / "sources.list",
        "Dir::Etc::sourceparts": "-",
        "Acquire::Retries": "2",
    }.items():
        options.extend(["-o", str(key) + "=" + str(value)])
    report("desktop", "Getting signed Ubuntu packages…")
    checked(["apt-get"] + options + ["update"])
    packages = ["jwm", "pcmanfm", "xterm", "mousepad", "galculator", "libnss3", "libnspr4", "libatk-bridge2.0-0", "libcups2", "libdrm2", "libxkbcommon0", "libxcomposite1", "libxdamage1", "libxrandr2", "libgbm1", "libasound2", "libgtk-3-0", "libxss1"]
    checked(["apt-get"] + options + ["--yes", "--download-only", "--no-install-recommends", "install"] + packages)
    report("desktop", "Installing the window manager and desktop tools…")
    for package in sorted(archives.glob("*.deb")):
        checked(["dpkg-deb", "-x", str(package), str(RUNTIME)], timeout=90)
    for program in ("jwm", "pcmanfm", "xterm", "mousepad", "galculator"):
        if not (RUNTIME / "usr/bin" / program).exists():
            raise RuntimeError("Desktop package did not supply " + program)
    marker.write_text(json.dumps({"packages": packages, "installed": time.time()}))


def install_firefox(report):
    binary = APPS / "firefox/firefox"
    if not binary.exists():
        report("firefox", "Downloading Firefox from Mozilla…")
        archive = DOWNLOADS / "firefox.tar.xz"
        fetch("https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US", archive)
        report("firefox", "Installing Firefox…")
        with tarfile.open(str(archive), "r:*") as tar:
            for member in tar.getmembers():
                target = (APPS / member.name).resolve()
                if os.path.commonpath([str(APPS.resolve()), str(target)]) != str(APPS.resolve()):
                    raise RuntimeError("Unexpected path in Firefox archive")
            tar.extractall(str(APPS))
        archive.unlink()
    report("firefox", "Installed")


def install_chrome(report):
    binary = APPS / "chrome/opt/google/chrome/google-chrome"
    if not binary.exists():
        report("chrome", "Downloading Google Chrome from Google…")
        archive = DOWNLOADS / "chrome.deb"
        fetch("https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb", archive)
        report("chrome", "Installing Google Chrome…")
        checked(["dpkg-deb", "-x", str(archive), str(APPS / "chrome")], timeout=120)
        archive.unlink()
    report("chrome", "Installed")


def write_icons():
    colors = {" ": "None", "a": "#59a6ff", "b": "#f2c35f", "c": "#ffffff", "d": "#111e34", "e": "#ed574a", "f": "#42b875", "g": "#f79539", "h": "#8e65e8"}
    svg_icons = {
        "files": '<path d="M5 10h8l2 2h12v12H5z" fill="#f2c35f"/><path d="M5 8h9l2 2H5z" fill="#ffe39a"/>',
        "firefox": '<circle cx="16" cy="16" r="12" fill="#ed574a"/><path d="M8 22c2-8 10-8 10-15 7 4 7 13 1 17-4 3-9 2-11-2z" fill="#f79539"/><circle cx="17" cy="17" r="5" fill="#8e65e8"/>',
        "chrome": '<circle cx="16" cy="16" r="12" fill="#f2c35f"/><path d="M16 16 8 29A14 14 0 0 1 4 13h12z" fill="#42b875"/><path d="M16 16H4A14 14 0 0 1 28 9l-6 10z" fill="#ed574a"/><circle cx="16" cy="16" r="6" fill="#59a6ff" stroke="#fff" stroke-width="2"/>',
        "roblox": '<rect x="5" y="5" width="22" height="22" rx="2" fill="#fff" transform="rotate(18 16 16)"/><rect x="13" y="13" width="6" height="6" fill="#111" transform="rotate(18 16 16)"/>',
        "terminal": '<rect x="4" y="5" width="24" height="22" rx="4" fill="#15243b" stroke="#59a6ff" stroke-width="2"/><path d="m10 12 4 4-4 4m8 0h5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
        "settings": '<path d="M14 3h4l1 4 3 2 4-1 2 4-3 3v4l3 3-2 4-4-1-3 2-1 4h-4l-1-4-3-2-4 1-2-4 3-3v-4l-3-3 2-4 4 1 3-2z" fill="#59a6ff" transform="translate(0 -2) scale(.94)"/><circle cx="16" cy="16" r="5" fill="#111"/>',
        "editor": '<rect x="7" y="4" width="18" height="24" rx="3" fill="#fff"/><path d="M11 11h10M11 16h10M11 21h7" stroke="#59a6ff" stroke-width="2"/>',
        "calculator": '<rect x="7" y="4" width="18" height="24" rx="3" fill="#15243b" stroke="#59a6ff" stroke-width="2"/><rect x="10" y="7" width="12" height="5" rx="1" fill="#fff"/><path d="M11 17h2m4 0h2m-8 5h2m4 0h2" stroke="#fff" stroke-width="2" stroke-linecap="round"/>',
        "trash": '<path d="M7 10h18l-2 17H9zM5 7h22M12 7l1-3h6l1 3" fill="#344963" stroke="#9dc7f5" stroke-width="2" stroke-linejoin="round"/><path d="M13 13v9m6-9v9" stroke="#9dc7f5" stroke-width="2"/>',
        "lock": '<rect x="7" y="14" width="18" height="14" rx="2" fill="#30445e" stroke="#9dc7f5" stroke-width="2"/><path d="M11 14V9a5 5 0 0 1 10 0v5" fill="none" stroke="#9dc7f5" stroke-width="2"/><circle cx="16" cy="20" r="2" fill="#fff"/>',
        "volume": '<path d="M4 13h6l7-6v18l-7-6H4z" fill="#365b82" stroke="#a9d2ff" stroke-width="2" stroke-linejoin="round"/><path d="M21 12a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14" fill="none" stroke="#a9d2ff" stroke-width="2"/>',
        "display": '<rect x="3" y="5" width="26" height="19" rx="2" fill="#263b55" stroke="#9dc7f5" stroke-width="2"/><path d="M11 28h10m-5-4v4" stroke="#9dc7f5" stroke-width="2"/>',
        "start": '<path d="M5 5h10v10H5zm12 0h10v10H17zM5 17h10v10H5zm12 0h10v10H17z" fill="#69a7e8"/>'
    }
    for name, artwork in svg_icons.items():
        (BASE / "icons" / (name + ".svg")).write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">' + artwork + '</svg>')
    for name in ("files", "firefox", "chrome", "roblox", "terminal", "settings", "editor", "calculator", "trash", "lock", "volume", "display", "start"):
        rows = []
        for y in range(32):
            row = ""
            for x in range(32):
                px, py = x - 15.5, y - 15.5
                radius = math.hypot(px, py)
                color = " "
                if name == "chrome" and radius < 14:
                    color = "e" if py < -abs(px) / 2 else ("f" if px < 0 else "b")
                    if radius < 7:
                        color = "c" if radius > 5.5 else "a"
                elif name == "firefox" and radius < 14:
                    color = "g" if radius > 9 or py > 2 else "h"
                elif name == "roblox":
                    u, v = px * .94 + py * .342, -px * .342 + py * .94
                    if abs(u) < 11 and abs(v) < 11 and not (abs(u) < 4 and abs(v) < 4):
                        color = "c"
                elif name == "files" and 4 <= x <= 28 and 10 <= y <= 26:
                    color = "b"
                elif name == "files" and 4 <= x <= 15 and 7 <= y <= 11:
                    color = "b"
                elif name == "terminal" and 3 <= x <= 28 and 5 <= y <= 27:
                    color = "a" if x in (3, 28) or y in (5, 27) else "d"
                    if (8 <= x <= 13 and abs((y-15) - (x-11)) < 1.5) or (8 <= x <= 13 and abs((y-15) + (x-11)) < 1.5) or (17 <= x <= 23 and y == 21):
                        color = "c"
                elif name == "settings" and 6 < radius < 12:
                    color = "a"
                elif name == "editor" and 7 <= x <= 25 and 4 <= y <= 28:
                    color = "c" if not (11 <= x <= 21 and y in (12, 17, 22)) else "a"
                elif name == "calculator" and 7 <= x <= 25 and 3 <= y <= 28:
                    color = "a" if y < 11 else ("c" if x % 5 in (1, 2) and y % 5 in (1, 2) else "d")
                elif name == "trash" and 7 <= x <= 25 and 10 <= y <= 27:
                    color = "a" if x in (7, 24, 25) or y in (10, 11, 26, 27) else "d"
                elif name == "lock" and ((7 <= x <= 25 and 14 <= y <= 27) or (11 <= x <= 21 and 6 <= y <= 16)):
                    color = "a" if x in (7, 8, 24, 25) or y in (14, 15, 26, 27) else "d"
                elif name == "volume" and 4 <= x <= 27 and 8 <= y <= 24:
                    color = "a" if x < 18 or (x < 25 and abs(y - 16) < (x - 18)) else "d"
                elif name == "display" and 3 <= x <= 28 and 5 <= y <= 24:
                    color = "a" if x in (3, 4, 27, 28) or y in (5, 6, 23, 24) else "d"
                elif name == "display" and 12 <= x <= 20 and 25 <= y <= 28:
                    color = "a"
                elif name == "start" and 5 <= x <= 26 and 5 <= y <= 26:
                    color = "a" if x in (5, 6, 15, 16, 25, 26) or y in (5, 6, 15, 16, 25, 26) else "d"
                row += color
            rows.append(row)
        lines = ['/* XPM */', 'static char * icon[] = {', '"32 32 {} 1",'.format(len(colors))]
        lines += ['"{} c {}",'.format(k, v) for k, v in colors.items()]
        lines += ['"{}"{}'.format(row, ',' if i < 31 else '};') for i, row in enumerate(rows)]
        (BASE / "icons" / (name + ".xpm")).write_text("\n".join(lines))


def command(action):
    return " ".join(shlex.quote(v) for v in (sys.executable, str(BASE / "launcher.py"), action))


def write_jwm():
    # CodeHS may execute main.py through a runner. A separate, tiny launcher
    # gives the window manager a stable executable file of its own.
    (BASE / "launcher.py").write_text(
        "import socket,sys,json\n"
        "s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)\n"
        "s.settimeout(5)\n"
        "s.connect(" + repr(str(SOCKET)) + ")\n"
        "s.sendall((json.dumps({'action':sys.argv[1]})+'\\n').encode())\n"
        "s.recv(4096)\n"
        "s.close()\n")
    entries = [("start", "App Launcher"), ("files", "Files"), ("trash", "Recycle Bin"), ("firefox", "Firefox"), ("chrome", "Google Chrome"), ("roblox", "Roblox (website)"), ("terminal", "Terminal"), ("editor", "Text Editor"), ("calculator", "Calculator"), ("controls", "Display and Volume"), ("lock", "Lock Screen"), ("settings", "Settings"), ("about", "About Sandboxed VM")]
    menu = "".join('<Program label="{}" icon="{}">{}</Program>'.format(label, BASE / "icons" / (("settings" if app == "about" else "display" if app == "controls" else app) + ".xpm"), escape(command(app))) for app, label in entries)
    buttons = "".join('<TrayButton popup="{}" icon="{}">exec:{}</TrayButton>'.format(label, BASE / "icons" / (app + ".xpm"), escape(command(app))) for app, label in entries[:5])
    xml = '''<?xml version="1.0"?>
<JWM>
<RootMenu onroot="123" labeled="true" label="Sandboxed VM" height="30">{menu}<Separator/><Program label="Stop desktop">{stop}</Program></RootMenu>
<Group><Class>SandboxedVMDesktop</Class><Option>noborder</Option><Option>notitle</Option><Option>nolist</Option><Option>sticky</Option><Option>layer:below</Option></Group>
<WindowStyle><Font>DejaVu Sans-10</Font><Width>2</Width><Height>30</Height><Corner>3</Corner><Foreground>#f2f2f2</Foreground><Background>#171717</Background><Outline>#303030</Outline><Active><Foreground>#ffffff</Foreground><Background>#252525</Background><Outline>#555555</Outline></Active></WindowStyle>
<TrayStyle><Font>DejaVu Sans-10</Font><Background>#080808</Background><Foreground>#eeeeee</Foreground><Outline>#222222</Outline><Active><Foreground>#ffffff</Foreground><Background>#292929</Background></Active></TrayStyle>
<MenuStyle><Font>DejaVu Sans-10</Font><Foreground>#eeeeee</Foreground><Background>#141414</Background><Outline>#333333</Outline><Active><Foreground>#ffffff</Foreground><Background>#303030</Background></Active></MenuStyle>
<Tray x="0" y="-1" height="44" autohide="off"><TrayButton label="Start" width="76">root:1</TrayButton><Spacer width="6"/>{buttons}<Spacer width="8"/><TaskList maxwidth="180"/><Clock format="%H:%M" width="70"/></Tray>
<Desktops width="1" height="1"/><FocusModel>click</FocusModel><MoveMode>opaque</MoveMode><ResizeMode>opaque</ResizeMode>
<Key mask="A" key="F4">close</Key><Key mask="A" key="Tab">nextstacked</Key><Key mask="4" key="space">exec:{start}</Key><Key mask="4" key="e">exec:{files}</Key><Key mask="C4" key="t">exec:{terminal}</Key><Key key="F1">exec:{about}</Key>
</JWM>'''.format(menu=menu, buttons=buttons, stop=escape(command("stop")), files=escape(command("files")), terminal=escape(command("terminal")), about=escape(command("about")), start=escape(command("start")))
    (BASE / "jwmrc").write_text(xml)


def resize_display():
    # Xvfb supplies the remote Linux screen; ask its normal RandR interface for
    # a desktop-sized mode. Browsers and the window manager use that real screen.
    try:
        modeline = subprocess.check_output(["gtf", "1024", "480", "60"], timeout=5, text=True)
        line = next(line for line in modeline.splitlines() if "Modeline" in line)
        values = shlex.split(line.strip())[2:]
        mode = "SandboxedVM-1024x480"
        for args in (["--newmode", mode] + values, ["--addmode", "screen", mode], ["--output", "screen", "--mode", mode]):
            subprocess.run(["xrandr"] + args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except (OSError, subprocess.SubprocessError, StopIteration):
        pass


class Desktop:
    def __init__(self):
        self.events = queue.Queue()
        self.processes = []
        self.ready = False
        self.closed = False
        self.namespace_sandbox = False
        self.status = {"desktop": "Preparing…", "firefox": "Waiting…", "chrome": "Waiting…"}
        self.failures = {}
        self.config = {"wallpaper": "Black", "browser": "Firefox"}
        try:
            self.config.update(json.loads((BASE / "settings.json").read_text()))
        except (OSError, ValueError):
            pass
        resize_display()
        self.root = tk.Tk(className="SandboxedVMDesktop")
        self.root.title(TITLE)
        self.root.wm_attributes("-type", "desktop")
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        self.root.geometry("{}x{}+0+0".format(self.width, self.height))
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg="#0b1427")
        self.canvas.pack(fill="both", expand=True)
        self.root.bind("<Configure>", lambda e: self.draw_wallpaper() if e.widget == self.root else None)
        self.root.bind_all("<Control-Alt-t>", lambda e: self.launch("terminal"))
        self.canvas.bind("<Button-3>", self.desktop_menu)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.draw_wallpaper()
        self.shortcuts = []
        self.create_shortcuts()
        self.welcome = None
        self.show_welcome()
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if SOCKET.exists():
            SOCKET.unlink()
        self.server.bind(str(SOCKET))
        os.chmod(str(SOCKET), 0o600)
        self.server.listen(8)
        threading.Thread(target=self.listen, daemon=True).start()
        threading.Thread(target=self.console_commands, daemon=True).start()
        threading.Thread(target=self.prepare, daemon=True).start()
        self.root.after(120, self.pump)
        self.last_heartbeat = time.monotonic()
        self.root.after(1000, self.watch_display)
        atexit.register(self.cleanup)

    def report(self, app, text):
        print("[{}] {}".format(app, text), flush=True)
        self.events.put(("status", app, text))

    def prepare(self):
        try:
            install_desktop(self.report)
            write_icons()
            write_jwm()
            checked([str(RUNTIME / "usr/bin/jwm"), "-p", "-f", str(BASE / "jwmrc")], env=environment())
            os.chmod(str(BASE / "run"), 0o700)
            if not (BASE / "run/bus").exists():
                self.spawn("dbus", ["dbus-daemon", "--session", "--nofork", "--nopidfile", "--address=unix:path=" + str(BASE / "run/bus")])
            manager = self.spawn("jwm", [str(RUNTIME / "usr/bin/jwm"), "-f", str(BASE / "jwmrc")])
            time.sleep(1)
            if manager.poll() is not None:
                raise RuntimeError("Window manager could not start. " + (LOGS / "jwm.log").read_text(errors="replace")[-1000:])
            self.events.put(("ready",))
            self.report("desktop", "Ready")
            try:
                probe = subprocess.run(["unshare", "--user", "--map-root-user", "true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                self.namespace_sandbox = probe.returncode == 0
            except (OSError, subprocess.SubprocessError):
                pass
            print("Chrome namespace sandbox available:", self.namespace_sandbox, flush=True)
            self.write_welcome_file()
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = {pool.submit(install_firefox, self.report): "firefox", pool.submit(install_chrome, self.report): "chrome"}
                for future, app in futures.items():
                    try:
                        future.result()
                    except Exception as exc:
                        self.report(app, "Installation failed")
                        self.events.put(("failure", app, str(exc)))
            self.events.put(("finished",))
        except Exception as exc:
            self.events.put(("failure", "desktop", str(exc)))

    def write_welcome_file(self):
        target = DOCUMENTS / "Welcome to Sandboxed VM.txt"
        if not target.exists():
            target.write_text("Sandboxed VM\nMade by 2pro12342\n\nThis is a real Linux desktop running in a CodeHS sandbox.\n\nFirefox and Google Chrome are native applications. The built-in Files app previews documents and includes a Recycle Bin. Text Editor and Calculator are native Linux programs; Terminal opens in a desktop popup.\n\nRoblox opens the Roblox website. Roblox has no supported native Linux desktop client, so gameplay is not included.\n\nUse Start, the desktop shortcuts, or the taskbar to open apps. Right-click the desktop for quick actions. The Start menu includes search and pinned apps; Display and Volume offers available resolution and audio controls. The lock screen is a convenience screen, not password security.\n\nSave documents in this Documents folder. Use Settings > Create backup to create a ZIP in the CodeHS program directory. Download important work; CodeHS can recycle the running server.\n\nIf the runtime is reset, press Run again and allow the applications to reinstall.\n")

    def spawn(self, name, args):
        log = (LOGS / (name + ".log")).open("ab", buffering=0)
        try:
            process = subprocess.Popen(args, env=environment(), cwd=str(DOCUMENTS), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        finally:
            log.close()
        self.processes.append((name, process))
        return process

    def listen(self):
        while not self.closed:
            try:
                connection, _ = self.server.accept()
                with connection:
                    connection.settimeout(3)
                    request = json.loads(connection.recv(4096).decode())
                    action = request.get("action", "")
                    if action == "status":
                        result = {"name": TITLE, "author": AUTHOR, "ready": self.ready, "apps": dict(self.status), "failures": dict(self.failures), "processes": {name: process.poll() for name, process in self.processes}}
                        connection.sendall(json.dumps(result).encode())
                    else:
                        self.events.put(("launch", action))
                        connection.sendall(b'{"accepted":true}')
            except (OSError, ValueError):
                if self.closed:
                    return

    def console_commands(self):
        # The CodeHS console also provides a convenient app launcher.
        for line in sys.stdin:
            action = line.strip().lower()
            if action == "status":
                print(json.dumps({"name": TITLE, "author": AUTHOR, "apps": self.status, "screen": [self.width, self.height], "chrome_namespace_sandbox": self.namespace_sandbox, "processes": {name: process.poll() for name, process in self.processes}, "failures": self.failures}), flush=True)
            elif action in ("firefox", "chrome", "roblox", "files", "trash", "start", "controls", "lock", "terminal", "editor", "calculator", "settings", "about"):
                self.events.put(("launch", action))

    def watch_display(self):
        if self.closed:
            return
        try:
            info = subprocess.check_output(["xrandr", "--current"], text=True, timeout=3, stderr=subprocess.DEVNULL)
            match = re.search(r"current (\d+) x (\d+)", info)
            if match:
                size = tuple(int(value) for value in match.groups())
                if size != (self.width, self.height):
                    self.width, self.height = size
                    self.root.geometry("{}x{}+0+0".format(*size))
                    self.root.lower()
                    self.position_shortcuts()
                    self.draw_wallpaper()
        except (OSError, subprocess.SubprocessError):
            pass
        if time.monotonic() - self.last_heartbeat > 20:
            print("Sandboxed VM session active. Console commands: status, firefox, chrome, files, terminal.", flush=True)
            self.last_heartbeat = time.monotonic()
        self.root.after(1000, self.watch_display)

    def pump(self):
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            if event[0] == "status":
                self.status[event[1]] = event[2]
                self.refresh_welcome()
            elif event[0] == "ready":
                self.ready = True
                self.root.lower()
                if self.welcome and self.welcome.winfo_exists():
                    self.welcome.lift()
            elif event[0] == "failure":
                self.failures[event[1]] = event[2]
                print("ERROR:", event[1], event[2], flush=True)
                self.refresh_welcome()
                self.notice("Setup needs attention", event[1] + ": " + event[2][-1600:])
            elif event[0] == "launch":
                self.launch(event[1])
            elif event[0] == "terminal-result":
                output, text, entry = event[1:]
                try:
                    if output.winfo_exists():
                        output.configure(state="normal")
                        output.insert("end", text + ("\n" if not text.endswith("\n") else ""))
                        output.see("end")
                        output.configure(state="disabled")
                    if entry.winfo_exists():
                        entry.configure(state="normal")
                        entry.focus_set()
                except tk.TclError:
                    pass
            elif event[0] == "finished":
                self.refresh_welcome()
                print("DESKTOP READY — Sandboxed VM — Made with ❤ by2pro12342", flush=True)
        if not self.closed:
            self.root.after(150, self.pump)

    def draw_wallpaper(self):
        canvas = self.canvas
        canvas.delete("wallpaper")
        width = max(1, self.root.winfo_width())
        height = max(1, self.root.winfo_height())
        # Near-black wallpaper with subtle charcoal curves for a clean Windows-like desktop.
        palette = {"Black": ("#050505", "#111111", "#1b1b1b"), "Blue": ("#091322", "#15365a", "#3479c5"), "Violet": ("#100d20", "#302052", "#8054bd"), "Forest": ("#071a1b", "#164344", "#31a18d")}
        background, mid, accent = palette.get(self.config["wallpaper"], palette["Black"])
        canvas.configure(bg=background)
        for index in range(24, 0, -1):
            inset = index * max(width, height) / 26
            canvas.create_oval(width * .66 - inset, height * .30 - inset * .60, width * 1.35 + inset, height * 1.48 + inset * .60, fill=mid if index > 11 else accent, outline=background, width=2, tags="wallpaper")
        canvas.create_oval(width * .70, height * .12, width * 1.22, height * .90, outline="#3a3a3a", width=1, tags="wallpaper")
        canvas.create_text(width - 38, height - 105, text="SANDBOXED VM", fill="#f0f0f0", font=("DejaVu Sans", 24, "bold"), anchor="e", tags="wallpaper")
        canvas.create_text(width - 39, height - 72, text="A little Linux desktop, made by " + AUTHOR, fill="#a0a0a0", font=("DejaVu Sans", 11), anchor="e", tags="wallpaper")
        canvas.create_text(width - 39, height - 38, text="READY WHEN YOU ARE", fill="#c8c8c8", font=("DejaVu Sans", 8, "bold"), anchor="e", tags="wallpaper")
        canvas.tag_lower("wallpaper")

    def desktop_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, bg="#202020", fg="#eeeeee", activebackground="#31577f", activeforeground="#ffffff")
        menu.add_command(label="Start", command=lambda: self.launch("start"))
        menu.add_command(label="Refresh desktop", command=self.draw_wallpaper)
        menu.add_separator()
        menu.add_command(label="Open Files", command=lambda: self.launch("files"))
        menu.add_command(label="Open Recycle Bin", command=lambda: self.launch("trash"))
        menu.add_command(label="Display and volume", command=lambda: self.launch("controls"))
        menu.add_command(label="Personalize", command=self.settings)
        menu.add_separator()
        menu.add_command(label="Lock screen", command=lambda: self.launch("lock"))
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()

    def start_menu(self):
        window = self.make_window("Start — Sandboxed VM", 440, 520)
        window.configure(bg="#151515")
        pane = tk.Frame(window, bg="#151515", padx=18, pady=16)
        pane.pack(fill="both", expand=True)
        tk.Label(pane, text="Start", bg="#151515", fg="#f5f5f5", font=("DejaVu Sans", 20, "bold"), anchor="w").pack(fill="x")
        search = tk.Entry(pane, bg="#242424", fg="#ffffff", insertbackground="#ffffff", relief="flat", font=("DejaVu Sans", 11))
        search.pack(fill="x", pady=(12, 10), ipady=8)
        tk.Label(pane, text="PINNED", bg="#151515", fg="#9a9a9a", font=("DejaVu Sans", 8, "bold"), anchor="w").pack(fill="x", pady=(0, 5))
        pinned = tk.Frame(pane, bg="#151515")
        pinned.pack(fill="x", pady=(0, 10))
        for index, (action, label) in enumerate((("files", "Files"), ("firefox", "Firefox"), ("editor", "Text Editor"), ("calculator", "Calculator"), ("settings", "Settings"), ("trash", "Recycle Bin"))):
            tk.Button(pinned, text=label, command=lambda name=action: (window.destroy(), self.launch(name)), bg="#242424", fg="#eeeeee", activebackground="#31577f", activeforeground="#ffffff", relief="flat", padx=8, pady=7).grid(row=index // 3, column=index % 3, sticky="ew", padx=(0, 5), pady=3)
        for column in range(3):
            pinned.grid_columnconfigure(column, weight=1)
        apps = [("Files", "files"), ("Firefox", "firefox"), ("Google Chrome", "chrome"), ("Roblox website", "roblox"), ("Terminal", "terminal"), ("Text Editor", "editor"), ("Calculator", "calculator"), ("Settings", "settings"), ("Display and volume", "controls"), ("Recycle Bin", "trash")]
        listing = tk.Listbox(pane, bg="#202020", fg="#eeeeee", selectbackground="#31577f", relief="flat", font=("DejaVu Sans", 10), activestyle="none", height=10)
        listing.pack(fill="both", expand=True)

        def refresh(_event=None):
            query = search.get().strip().lower()
            listing.delete(0, "end")
            for label, action in apps:
                if query in label.lower():
                    listing.insert("end", label)

        def open_selected(_event=None):
            selected = listing.curselection()
            if not selected:
                return
            label = listing.get(selected[0])
            for app_label, action in apps:
                if app_label == label:
                    window.destroy()
                    self.launch(action)
                    break

        search.bind("<KeyRelease>", refresh)
        listing.bind("<Double-Button-1>", open_selected)
        listing.bind("<Return>", open_selected)
        listing.bind("<Button-1>", lambda _event: None)
        refresh()
        footer = tk.Frame(pane, bg="#151515")
        footer.pack(fill="x", pady=(10, 0))
        tk.Button(footer, text="Open selected app", command=open_selected, bg="#31577f", fg="white", relief="flat", padx=10, pady=6).pack(side="left")
        tk.Button(footer, text="Lock", command=lambda: (window.destroy(), self.launch("lock")), bg="#242424", fg="white", relief="flat", padx=12, pady=6).pack(side="right")
        search.focus_set()

    def file_manager(self, in_trash=False):
        window = self.make_window("Recycle Bin" if in_trash else "Files — Documents", 760, 500)
        window.configure(bg="#151515")
        bar = tk.Frame(window, bg="#202020", padx=10, pady=8)
        bar.pack(fill="x")
        location = tk.StringVar(value="Recycle Bin" if in_trash else "Documents")
        tk.Label(bar, textvariable=location, bg="#202020", fg="#eeeeee", anchor="w").pack(side="left", fill="x", expand=True)
        body = tk.Frame(window, bg="#151515", padx=10, pady=10)
        body.pack(fill="both", expand=True)
        listing = tk.Listbox(body, bg="#202020", fg="#eeeeee", selectbackground="#31577f", relief="flat", width=30, activestyle="none")
        listing.pack(side="left", fill="both", expand=True, padx=(0, 10))
        preview = tk.Text(body, bg="#111111", fg="#d0d0d0", relief="flat", wrap="word", padx=12, pady=10, font=("DejaVu Sans Mono", 9))
        preview.pack(side="left", fill="both", expand=True)
        preview.insert("1.0", "Select a file to preview its contents.")
        preview.configure(state="disabled")
        current = [DOCUMENTS]
        items = []

        def show_preview(_event=None):
            selection = listing.curselection()
            text = "Select a file to preview its contents."
            if selection and selection[0] < len(items):
                path = items[selection[0]]
                if path.is_dir():
                    text = "Folder\n\nDouble-click to open this folder."
                else:
                    try:
                        text = path.read_text(errors="replace")[:12000]
                        if not text:
                            text = "This file is empty."
                    except (OSError, UnicodeError):
                        text = "Preview is unavailable for this file type.\n\n{} bytes".format(path.stat().st_size if path.exists() else 0)
            preview.configure(state="normal")
            preview.delete("1.0", "end")
            preview.insert("1.0", text)
            preview.configure(state="disabled")

        def refresh():
            listing.delete(0, "end")
            items[:] = sorted(TRASH.iterdir(), key=lambda path: path.name.lower()) if in_trash else sorted(current[0].iterdir(), key=lambda path: (not path.is_dir(), path.name.lower()))
            location.set("Recycle Bin" if in_trash else str(current[0].relative_to(DOCUMENTS) or "Documents"))
            if not in_trash and current[0] == DOCUMENTS:
                location.set("Documents")
            for path in items:
                listing.insert("end", ("[Folder] " if path.is_dir() else "[File] ") + path.name)
            show_preview()

        def open_item(_event=None):
            selection = listing.curselection()
            if not selection or selection[0] >= len(items):
                return
            path = items[selection[0]]
            if not in_trash and path.is_dir():
                current[0] = path
                refresh()
            elif not in_trash:
                try:
                    self.spawn("editor", [str(RUNTIME / "usr/bin/mousepad"), str(path)])
                except OSError as exc:
                    self.notice("Could not open file", str(exc))

        def move_selected():
            selection = listing.curselection()
            if not selection or selection[0] >= len(items):
                return
            path = items[selection[0]]
            if in_trash:
                original_name = path.name.split("__", 1)[-1]
                destination = DOCUMENTS / original_name
                if destination.exists():
                    destination = DOCUMENTS / (destination.stem + " (restored)" + destination.suffix)
                try:
                    shutil.move(str(path), str(destination))
                except OSError as exc:
                    self.notice("Could not restore item", str(exc))
            else:
                destination = TRASH / (str(int(time.time() * 1000)) + "__" + path.name)
                try:
                    shutil.move(str(path), str(destination))
                except OSError as exc:
                    self.notice("Could not move item", str(exc))
            refresh()

        listing.bind("<<ListboxSelect>>", show_preview)
        listing.bind("<Double-Button-1>", open_item)
        listing.bind("<Return>", open_item)
        actions = tk.Frame(window, bg="#151515", padx=10, pady=8)
        actions.pack(fill="x")
        if not in_trash:
            tk.Button(actions, text="Up", command=lambda: (current.__setitem__(0, current[0].parent) if current[0] != DOCUMENTS else None, refresh()), bg="#292929", fg="white", relief="flat", padx=12, pady=6).pack(side="left")
        tk.Button(actions, text="Restore" if in_trash else "Move to Recycle Bin", command=move_selected, bg="#31577f", fg="white", relief="flat", padx=12, pady=6).pack(side="left", padx=6)
        if in_trash:
            tk.Button(actions, text="Empty Recycle Bin", command=lambda: self.empty_trash(refresh), bg="#642f32", fg="white", relief="flat", padx=12, pady=6).pack(side="left")
        tk.Button(actions, text="Close", command=window.destroy, bg="#292929", fg="white", relief="flat", padx=12, pady=6).pack(side="right")
        refresh()

    def empty_trash(self, refresh):
        if not messagebox.askyesno("Empty Recycle Bin", "Permanently delete everything in the Recycle Bin?", parent=self.root):
            return
        for path in list(TRASH.iterdir()):
            try:
                shutil.rmtree(str(path)) if path.is_dir() else path.unlink()
            except OSError as exc:
                self.notice("Could not empty Recycle Bin", str(exc))
        refresh()

    def controls(self):
        window = self.make_window("Display and Volume", 500, 390)
        frame = tk.Frame(window, bg="#151515", padx=22, pady=20)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="Quick settings", bg="#151515", fg="#f2f2f2", font=("DejaVu Sans", 18, "bold")).pack(anchor="w", pady=(0, 18))
        tk.Label(frame, text="Display resolution", bg="#151515", fg="#cccccc").pack(anchor="w")
        modes = []
        try:
            info = subprocess.check_output(["xrandr", "--query"], env=environment(), stderr=subprocess.DEVNULL, text=True, timeout=4)
            modes = sorted(set(re.findall(r"^\s+(\d+x\d+)\s", info, re.M)))
        except (OSError, subprocess.SubprocessError):
            pass
        if not modes:
            modes = ["Unavailable"]
        mode = tk.StringVar(value="{}x{}".format(self.width, self.height) if "{}x{}".format(self.width, self.height) in modes else modes[0])
        tk.OptionMenu(frame, mode, *modes).pack(anchor="w", pady=(4, 8))

        def apply_display():
            if mode.get() == "Unavailable":
                self.notice("Display settings", "No adjustable display modes were reported.")
                return
            try:
                subprocess.run(["xrandr", "--output", "screen", "--mode", mode.get()], env=environment(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=5)
                self.width, self.height = [int(value) for value in mode.get().split("x")]
                self.root.geometry("{}x{}+0+0".format(self.width, self.height))
                self.position_shortcuts()
                self.draw_wallpaper()
            except (OSError, subprocess.SubprocessError) as exc:
                self.notice("Could not change resolution", str(exc))

        tk.Button(frame, text="Apply resolution", command=apply_display, bg="#31577f", fg="white", relief="flat", padx=10, pady=6).pack(anchor="w", pady=(0, 15))
        tk.Label(frame, text="Volume", bg="#151515", fg="#cccccc").pack(anchor="w")
        volume = tk.IntVar(value=60)
        tk.Scale(frame, from_=0, to=100, orient="horizontal", variable=volume, bg="#151515", fg="#eeeeee", troughcolor="#31577f", highlightthickness=0, length=340).pack(anchor="w", fill="x")

        def apply_volume():
            pactl = shutil.which("pactl", path=environment().get("PATH"))
            if not pactl:
                self.notice("Volume control unavailable", "This sandbox does not provide pactl or a system audio service.")
                return
            try:
                subprocess.run([pactl, "set-sink-volume", "@DEFAULT_SINK@", str(volume.get()) + "%"], env=environment(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=5)
                self.notice("Volume updated", "System volume set to {}%.".format(volume.get()))
            except (OSError, subprocess.SubprocessError) as exc:
                self.notice("Could not change volume", str(exc))

        tk.Button(frame, text="Apply volume", command=apply_volume, bg="#292929", fg="white", relief="flat", padx=10, pady=6).pack(anchor="w", pady=(10, 0))

    def lock_screen(self):
        window = tk.Toplevel(self.root)
        window.configure(bg="#080808")
        window.title("Locked")
        window.attributes("-fullscreen", True)
        window.attributes("-topmost", True)
        panel = tk.Frame(window, bg="#080808")
        panel.place(relx=0.5, rely=0.43, anchor="center")
        clock = tk.Label(panel, bg="#080808", fg="#ffffff", font=("DejaVu Sans", 48, "bold"))
        clock.pack()
        date = tk.Label(panel, text=time.strftime("%A, %B %d"), bg="#080808", fg="#b8b8b8", font=("DejaVu Sans", 16))
        date.pack(pady=(0, 26))
        tk.Label(panel, text="Sandboxed VM is locked", bg="#080808", fg="#9a9a9a", font=("DejaVu Sans", 11)).pack(pady=(0, 18))
        tk.Button(panel, text="Unlock desktop", command=window.destroy, bg="#31577f", fg="white", relief="flat", padx=20, pady=10).pack()

        def update_clock():
            if window.winfo_exists():
                clock.configure(text=time.strftime("%H:%M"))
                window.after(1000, update_clock)

        window.bind("<Escape>", lambda _event: window.destroy())
        update_clock()

    def create_shortcuts(self):
        shortcut_data = [
            ("files", "Files", "#ffd06e"), ("firefox", "Firefox", "#ff9b48"),
            ("chrome", "Chrome", "#66b2ff"), ("roblox", "Roblox Web", "#ffffff"),
            ("terminal", "Terminal", "#b5d5ff"), ("settings", "Settings", "#b5c8e6"),
            ("trash", "Recycle Bin", "#a9d2ff"), ("start", "Apps", "#8fc2ff")
        ]
        for action, label, color in shortcut_data:
            tile = tk.Frame(self.root, bg="#171717", highlightthickness=1, highlightbackground="#344a66", cursor="hand2")
            icon = tk.Canvas(tile, width=42, height=42, bg="#171717", highlightthickness=0)
            icon.pack(pady=(4, 0))
            if action == "files":
                icon.create_rectangle(6, 14, 36, 35, fill="#f2c35f", outline="")
                icon.create_rectangle(7, 10, 20, 16, fill="#ffe39a", outline="")
            elif action in ("firefox", "chrome"):
                icon.create_oval(5, 5, 37, 37, fill="#ed574a" if action == "firefox" else "#f2c35f", outline="")
                if action == "firefox":
                    icon.create_arc(8, 7, 36, 36, start=205, extent=230, fill="#f79539", outline="", style="pieslice")
                    icon.create_oval(18, 18, 29, 29, fill="#8e65e8", outline="")
                else:
                    icon.create_arc(5, 5, 37, 37, start=30, extent=115, fill="#42b875", outline="", style="pieslice")
                    icon.create_oval(15, 15, 27, 27, fill="#59a6ff", outline="#ffffff", width=2)
            elif action == "roblox":
                icon.create_polygon(15, 7, 35, 15, 27, 35, 7, 27, fill="#ffffff", outline="")
                icon.create_polygon(17, 17, 25, 20, 22, 28, 14, 25, fill="#111111", outline="")
            elif action == "terminal":
                icon.create_rectangle(5, 7, 37, 35, fill="#15243b", outline="#59a6ff", width=2)
                icon.create_text(19, 21, text=">_", fill="#ffffff", font=("DejaVu Sans Mono", 13, "bold"))
            else:
                icon.create_oval(9, 9, 33, 33, fill="#59a6ff", outline="")
                icon.create_oval(16, 16, 26, 26, fill="#171717", outline="")
                for angle in range(0, 360, 45):
                    icon.create_line(21, 4, 21, 10, fill="#b5c8e6", width=3)
                    icon.create_line(21, 32, 21, 38, fill="#b5c8e6", width=3)
                    icon.create_line(4, 21, 10, 21, fill="#b5c8e6", width=3)
                    icon.create_line(32, 21, 38, 21, fill="#b5c8e6", width=3)
                    break
            caption = tk.Label(tile, text=label, bg="#171717", fg=color, font=("DejaVu Sans", 9, "bold"), cursor="hand2")
            caption.pack(fill="x", pady=(0, 5))
            for widget in (tile, icon, caption):
                widget.bind("<Button-1>", lambda event, name=action: self.launch(name))
                widget.bind("<Enter>", lambda event, frame=tile, canvas=icon, text=caption: (frame.configure(bg="#203956", highlightbackground="#83b7ff"), canvas.configure(bg="#203956"), text.configure(bg="#203956")))
                widget.bind("<Leave>", lambda event, frame=tile, canvas=icon, text=caption: (frame.configure(bg="#171717", highlightbackground="#344a66"), canvas.configure(bg="#171717"), text.configure(bg="#171717")))
            self.shortcuts.append(tile)
        self.position_shortcuts()

    def position_shortcuts(self):
        rows = max(1, (self.height - 64) // 86)
        for index, shortcut in enumerate(self.shortcuts):
            shortcut.place(x=16 + (index // rows) * 124, y=18 + (index % rows) * 86, width=112, height=72)

    def make_window(self, title, width=600, height=440):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.configure(bg="#111111")
        width = min(width, max(320, self.width - 150))
        height = min(height, max(260, self.height - 68))
        x = min(max(138, (self.width - width) // 2), max(0, self.width - width - 10))
        y = max(10, (self.height - height - 44) // 2)
        window.geometry("{}x{}+{}+{}".format(width, height, x, y))
        window.minsize(min(320, width), min(260, height))
        window.lift()
        return window

    def show_welcome(self):
        if self.welcome and self.welcome.winfo_exists():
            self.welcome.deiconify()
            self.welcome.lift()
            return
        self.welcome = self.make_window("Welcome to Sandboxed VM", 760, 500)
        self.welcome.configure(bg="#111111")
        pane = tk.Frame(self.welcome, bg="#111111", padx=22, pady=18)
        pane.pack(fill="both", expand=True)

        hero = tk.Frame(pane, bg="#1c1c1c", padx=20, pady=14)
        hero.pack(fill="x", pady=(0, 14))
        tk.Label(hero, text="Welcome back.", bg="#1c1c1c", fg="#f5f5f5", font=("DejaVu Sans", 20, "bold"), anchor="w").pack(fill="x")
        tk.Label(hero, text="Your desktop is ready for whatever you want to do next.", bg="#1c1c1c", fg="#b0b0b0", font=("DejaVu Sans", 10), anchor="w").pack(fill="x", pady=(3, 0))

        content = tk.Frame(pane, bg="#111111")
        content.pack(fill="both", expand=True)
        apps = tk.Frame(content, bg="#111111")
        apps.pack(side="left", fill="both", expand=True, padx=(0, 16))
        tk.Label(apps, text="QUICK LAUNCH", bg="#111111", fg="#a0a0a0", font=("DejaVu Sans", 9, "bold"), anchor="w").pack(fill="x", pady=(0, 7))
        cards = tk.Frame(apps, bg="#111111")
        cards.pack(fill="both", expand=True)
        for index, (action, title, detail, color) in enumerate((
            ("firefox", "Firefox", "Browse the web", "#e97837"),
            ("chrome", "Google Chrome", "Browse with Chrome", "#397ac4"),
            ("files", "File manager", "Open your Documents", "#bd8b28"),
            ("editor", "Text Editor", "Write and edit files", "#5479a8"),
            ("terminal", "Terminal", "Use the Linux shell", "#465f86"),
            ("settings", "Personalize", "Wallpaper and options", "#735ca7"),
        )):
            card = tk.Frame(cards, bg="#1b1b1b", highlightthickness=1, highlightbackground="#333333")
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=(0, 8), pady=(0, 8))
            tk.Label(card, text="●", bg="#1b1b1b", fg=color, font=("DejaVu Sans", 16), anchor="w").pack(fill="x", padx=11, pady=(6, 0))
            tk.Label(card, text=title, bg="#1b1b1b", fg="#f0f0f0", font=("DejaVu Sans", 10, "bold"), anchor="w").pack(fill="x", padx=12)
            tk.Label(card, text=detail, bg="#1b1b1b", fg="#aaaaaa", font=("DejaVu Sans", 8), anchor="w").pack(fill="x", padx=12, pady=(1, 8))
            card.bind("<Button-1>", lambda event, name=action: self.launch(name))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda event, name=action: self.launch(name))
            card.bind("<Enter>", lambda event, widget=card: widget.configure(highlightbackground="#777777", bg="#242424"))
            card.bind("<Leave>", lambda event, widget=card: widget.configure(highlightbackground="#333333", bg="#1b1b1b"))
            for child in card.winfo_children():
                child.bind("<Enter>", lambda event, widget=card: widget.configure(highlightbackground="#82a9d8"))
                child.bind("<Leave>", lambda event, widget=card: widget.configure(highlightbackground="#d9e2ee"))
        for column in range(2):
            cards.grid_columnconfigure(column, weight=1, uniform="app-card")
        for row in range(3):
            cards.grid_rowconfigure(row, weight=1, uniform="app-card")

        side = tk.Frame(content, bg="#1b1b1b", padx=14, pady=12, highlightthickness=1, highlightbackground="#333333")
        side.pack(side="right", fill="y")
        tk.Label(side, text="SYSTEM STATUS", bg="#1b1b1b", fg="#a0a0a0", font=("DejaVu Sans", 9, "bold"), anchor="w").pack(fill="x", pady=(0, 8))
        self.status_vars = {}
        for app, label in (("desktop", "Desktop tools"), ("firefox", "Firefox"), ("chrome", "Chrome")):
            row = tk.Frame(side, bg="#1b1b1b")
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label, bg="#1b1b1b", fg="#dddddd", font=("DejaVu Sans", 9, "bold"), anchor="w").pack(fill="x")
            variable = tk.StringVar(value=self.status[app])
            self.status_vars[app] = variable
            tk.Label(row, textvariable=variable, bg="#1b1b1b", fg="#aaaaaa", font=("DejaVu Sans", 8), anchor="w", wraplength=150, justify="left").pack(fill="x", pady=(2, 0))
        tk.Frame(side, bg="#333333", height=1).pack(fill="x", pady=9)
        tk.Label(side, text="Roblox opens the website.\nNative gameplay is not\nsupported on Linux.", bg="#1b1b1b", fg="#aaaaaa", font=("DejaVu Sans", 8), justify="left", anchor="w").pack(fill="x")
        tk.Button(side, text="Choose a wallpaper", command=self.settings, bg="#edf3fb", fg="#31577f", activebackground="#dce9f8", relief="flat", padx=9, pady=6, cursor="hand2").pack(anchor="w", pady=(10, 0))

        tk.Label(pane, text="SANDBOXED VM  ·  MADE BY " + AUTHOR.upper(), bg="#111111", fg="#777777", font=("DejaVu Sans", 8, "bold"), anchor="e").pack(fill="x", pady=(8, 0))

    def refresh_welcome(self):
        if self.welcome and self.welcome.winfo_exists():
            for app, variable in self.status_vars.items():
                variable.set(self.status[app])

    def notice(self, title, text):
        window = self.make_window(title, 620, 330)
        tk.Label(window, text=title, bg="#111111", fg="#f0f0f0", font=("DejaVu Sans", 17, "bold"), anchor="w").pack(fill="x", padx=24, pady=(22, 10))
        body = tk.Text(window, wrap="word", bg="#111111", fg="#cccccc", relief="flat", padx=24, pady=8, font=("DejaVu Sans", 10))
        body.pack(fill="both", expand=True)
        body.insert("1.0", text)
        body.configure(state="disabled")
        tk.Button(window, text="Close", command=window.destroy, padx=20, pady=7).pack(pady=14)

    def launch(self, action):
        if action == "stop":
            self.close()
            return
        if action == "about":
            self.notice("About Sandboxed VM", "Sandboxed VM\nMade by 2pro12342\n\nA real Linux desktop session inside CodeHS.\n\nWindow manager: JWM\nFiles: built-in browser with preview and Recycle Bin\nTerminal: in-app command popup\nText editor: Mousepad\nCalculator: Galculator\nBrowsers: Firefox and Google Chrome\n\nThe lock screen is a convenience screen, not password security. Roblox is a website shortcut; native Roblox gameplay is not supported on Linux.\n\nThis project is a Linux sandbox desktop, not a Microsoft Windows installation.")
            return
        if action == "settings":
            self.settings()
            return
        if action == "start":
            self.start_menu()
            return
        if action == "trash":
            self.file_manager(in_trash=True)
            return
        if action == "controls":
            self.controls()
            return
        if action == "lock":
            self.lock_screen()
            return
        if action == "files":
            self.file_manager()
            return
        if action == "terminal":
            self.terminal_popup()
            return
        if not self.ready:
            self.show_welcome()
            return
        args = None
        if action in ("chrome", "firefox", "roblox"):
            browser = self.config["browser"].lower() if action == "roblox" else action
            if self.status.get(browser) != "Installed":
                self.show_welcome()
                return
            url = "https://www.roblox.com/" if action == "roblox" else (DOCUMENTS / "Welcome to Sandboxed VM.txt").as_uri()
            profile = BASE / "profiles" / browser
            profile.mkdir(exist_ok=True)
            if browser == "firefox":
                args = [str(APPS / "firefox/firefox"), "--profile", str(profile), url]
            else:
                args = [str(APPS / "chrome/opt/google/chrome/google-chrome"), "--user-data-dir=" + str(profile), "--disable-dev-shm-usage", "--no-default-browser-check", url]
                # Use Chromium's unprivileged namespace sandbox when it works.
                # Seccomp and the namespace sandbox remain enabled in this
                # branch; the fallback below requires the explicit user option.
                if self.namespace_sandbox:
                    args.insert(1, "--disable-setuid-sandbox")
                elif ALLOW_CHROME_WITHOUT_SANDBOX:
                    args.insert(1, "--no-sandbox")
            name = browser
        else:
            name = action
            choices = {
                "files": [str(RUNTIME / "usr/bin/pcmanfm"), str(DOCUMENTS)],
                "editor": [str(RUNTIME / "usr/bin/mousepad"), str(DOCUMENTS / "Welcome to Sandboxed VM.txt")],
                "terminal": [str(RUNTIME / "usr/bin/xterm"), "-T", "Terminal — Sandboxed VM", "-fa", "DejaVu Sans Mono", "-fs", "11", "-bg", "#0c1628", "-fg", "#e4eeff", "-e", "/bin/bash"],
                "calculator": [str(RUNTIME / "usr/bin/galculator")],
            }
            args = choices.get(action)
        if not args:
            return
        try:
            process = self.spawn(name, args)
            self.root.lower()
            self.root.after(2400, lambda: self.check_launch(name, process))
        except OSError as exc:
            self.notice("Could not open " + action, str(exc))

    def terminal_popup(self):
        window = self.make_window("Terminal — Sandboxed VM", 650, 390)
        window.configure(bg="#0b0b0b")
        output = tk.Text(window, bg="#0b0b0b", fg="#d9e6f5", insertbackground="#ffffff", relief="flat", padx=14, pady=12, font=("DejaVu Sans Mono", 10), wrap="word")
        output.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        output.insert("end", "Sandboxed VM terminal · working directory: Documents\nType a command and press Enter. Commands stop after 30 seconds.\n\n")
        output.configure(state="disabled")
        entry = tk.Entry(window, bg="#191919", fg="#ffffff", insertbackground="#ffffff", relief="flat", font=("DejaVu Sans Mono", 10))
        entry.pack(fill="x", padx=8, pady=9, ipady=8)

        def submit(_event=None):
            command_text = entry.get().strip()
            if not command_text:
                return "break"
            entry.delete(0, "end")
            entry.configure(state="disabled")
            output.configure(state="normal")
            output.insert("end", "$ " + command_text + "\n")
            output.configure(state="disabled")
            output.see("end")

            def execute():
                try:
                    result = subprocess.run(["/bin/bash", "-lc", command_text], cwd=str(DOCUMENTS), env=environment(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
                    text = result.stdout.decode(errors="replace") or "(command finished with exit code {})".format(result.returncode)
                except subprocess.TimeoutExpired as exc:
                    text = (exc.stdout or b"").decode(errors="replace") + "\nCommand timed out after 30 seconds."
                except OSError as exc:
                    text = "Could not run command: " + str(exc)
                self.events.put(("terminal-result", output, text, entry))

            threading.Thread(target=execute, daemon=True).start()
            return "break"

        entry.bind("<Return>", submit)
        entry.focus_set()

    def check_launch(self, name, process):
        result = process.poll()
        if result is not None and result != 0:
            log = (LOGS / (name + ".log")).read_text(errors="replace")[-1800:]
            self.failures[name] = log
            print("LAUNCH ERROR:", name, log, flush=True)
            self.notice("Could not open " + name, "The real application exited with code {}.\n\n{}".format(result, log))

    def settings(self):
        window = self.make_window("Settings — Sandboxed VM", 510, 370)
        frame = tk.Frame(window, bg="#111111", padx=24, pady=22)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="Make it yours", font=("DejaVu Sans", 19, "bold"), bg="#111111", fg="#f0f0f0").pack(anchor="w", pady=(0, 18))
        tk.Label(frame, text="Wallpaper", bg="#111111", fg="#cccccc").pack(anchor="w")
        wallpaper = tk.StringVar(value=self.config["wallpaper"])
        tk.OptionMenu(frame, wallpaper, "Black", "Blue", "Violet", "Forest").pack(anchor="w", pady=(3, 10))
        tk.Label(frame, text="Browser for the Roblox website shortcut", bg="#111111", fg="#cccccc").pack(anchor="w")
        browser = tk.StringVar(value=self.config["browser"])
        tk.OptionMenu(frame, browser, "Firefox", "Chrome").pack(anchor="w", pady=(3, 12))
        def save():
            self.config.update(wallpaper=wallpaper.get(), browser=browser.get())
            (BASE / "settings.json").write_text(json.dumps(self.config))
            self.draw_wallpaper()
            window.destroy()
        row = tk.Frame(frame, bg="#f5f8ff")
        row.pack(anchor="w", pady=10)
        tk.Button(row, text="Save settings", command=save, padx=12, pady=7).pack(side="left", padx=(0, 10))
        tk.Button(row, text="Create document backup", command=self.backup, padx=12, pady=7).pack(side="left")

    def backup(self):
        import zipfile
        output = HERE / "Sandboxed-VM-Documents.zip"
        with zipfile.ZipFile(str(output), "w", zipfile.ZIP_DEFLATED) as archive:
            for filename in DOCUMENTS.rglob("*"):
                if filename.is_file() and not filename.is_symlink():
                    archive.write(str(filename), str(filename.relative_to(HERE)))
        self.notice("Backup created", "Your documents were saved to:\n\n" + str(output) + "\n\nEnable CodeHS File I/O to show generated files, then download this ZIP from the CodeHS file list.")

    def close(self):
        if not self.closed:
            self.closed = True
            self.cleanup()
            self.root.destroy()

    def cleanup(self):
        for _name, process in reversed(self.processes):
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        try:
            self.server.close()
            SOCKET.unlink(missing_ok=True)
        except (OSError, AttributeError):
            pass

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if "--launch" in sys.argv:
        position = sys.argv.index("--launch")
        sys.exit(client(sys.argv[position + 1] if len(sys.argv) > position + 1 else "status"))
    try:
        desktop = Desktop()
        signal.signal(signal.SIGTERM, lambda *_: desktop.root.after(0, desktop.close))
        desktop.run()
    except Exception as error:
        print("Sandboxed VM could not start:", error, flush=True)
        raise
