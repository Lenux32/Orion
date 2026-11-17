"""Sandboxed VM — Made by 2pro12342.

Run as main.py in a CodeHS Python Graphics (tkinter) sandbox.
This is a real Linux desktop session with native applications, not an OS mockup.
Packages are extracted into this program's own directory, without sudo.
Roblox is a website shortcut; a native Roblox Linux client is not included.
"""
import atexit
import calendar
import datetime
import json
import math
import os
import platform
from pathlib import Path
import queue
import random
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
from tkinter import filedialog, messagebox, simpledialog
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
for directory in (BASE, RUNTIME, DOWNLOADS, DOCUMENTS, LOGS, APPS, BASE / "profiles", BASE / "run", BASE / "icons"):
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
    for name in ("files", "firefox", "chrome", "roblox", "terminal", "settings", "editor", "calculator", "center", "notes"):
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
                elif name in ("center", "notes") and 7 <= x <= 24 and 6 <= y <= 26:
                    color = "a" if y in (6, 26) or x in (7, 24) else ("c" if name == "notes" and y in (12, 16, 20) and 11 <= x <= 20 else "d")
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
    entries = [("center", "Stark Center"), ("files", "Files"), ("firefox", "Firefox"), ("chrome", "Google Chrome"), ("roblox", "Roblox (website)"), ("terminal", "Terminal"), ("editor", "Text Editor"), ("calculator", "Calculator"), ("notes", "Notes"), ("settings", "Settings"), ("about", "About Sandboxed VM")]
    menu = "".join('<Program label="{}" icon="{}">{}</Program>'.format(label, BASE / "icons" / (app + ".xpm") if app != "about" else BASE / "icons/settings.xpm", escape(command(app))) for app, label in entries)
    buttons = "".join('<TrayButton popup="{}" icon="{}">exec:{}</TrayButton>'.format(label, BASE / "icons" / (app + ".xpm"), escape(command(app))) for app, label in entries[:5])
    xml = '''<?xml version="1.0"?>
<JWM>
<RootMenu onroot="123" labeled="true" label="Sandboxed VM" height="30">{menu}<Separator/><Program label="Stop desktop">{stop}</Program></RootMenu>
<Group><Class>SandboxedVMDesktop</Class><Option>noborder</Option><Option>notitle</Option><Option>nolist</Option><Option>sticky</Option><Option>layer:below</Option></Group>
<WindowStyle><Font>DejaVu Sans-10</Font><Width>2</Width><Height>30</Height><Corner>3</Corner><Foreground>#eaf2ff</Foreground><Background>#101114</Background><Outline>#292c32</Outline><Active><Foreground>#ffffff</Foreground><Background>#202329</Background><Outline>#626a77</Outline></Active></WindowStyle>
<TrayStyle><Font>DejaVu Sans-10</Font><Background>#08090b</Background><Foreground>#e5e8ed</Foreground><Outline>#202329</Outline><Active><Foreground>#ffffff</Foreground><Background>#202329</Background></Active></TrayStyle>
<MenuStyle><Font>DejaVu Sans-10</Font><Foreground>#e5e8ed</Foreground><Background>#0c0d10</Background><Outline>#30343c</Outline><Active><Foreground>#ffffff</Foreground><Background>#292d35</Background></Active></MenuStyle>
<Tray x="0" y="-1" height="44" autohide="off"><TrayButton label="Start" width="76">root:1</TrayButton><Spacer width="6"/>{buttons}<Spacer width="8"/><TaskList maxwidth="180"/><Clock format="%H:%M" width="70"/></Tray>
<Desktops width="2" height="2"/><FocusModel>click</FocusModel><MoveMode>opaque</MoveMode><ResizeMode>opaque</ResizeMode>
<Key mask="A" key="F4">close</Key><Key mask="A" key="Tab">nextstacked</Key><Key mask="4" key="e">exec:{files}</Key><Key mask="C4" key="t">exec:{terminal}</Key><Key mask="CA" key="space">exec:{center}</Key><Key mask="CA" key="n">exec:{notes}</Key><Key mask="A" key="F9">showdesktop</Key><Key key="F1">exec:{about}</Key>
</JWM>'''.format(menu=menu, buttons=buttons, stop=escape(command("stop")), files=escape(command("files")), terminal=escape(command("terminal")), center=escape(command("center")), notes=escape(command("notes")), about=escape(command("about")))
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
        self.config = {"wallpaper": "Stark", "browser": "Firefox", "particle_density": 70, "particle_speed": 1.0, "icon_size": 62, "show_welcome": True}
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
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg="#030405")
        self.canvas.pack(fill="both", expand=True)
        self.root.bind("<Configure>", lambda e: self.draw_wallpaper() if e.widget == self.root else None)
        self.root.bind_all("<Control-Alt-t>", lambda e: self.launch("terminal"))
        self.root.bind_all("<Control-Alt-space>", lambda e: self.launch("center"))
        self.root.bind_all("<Control-Alt-l>", lambda e: self.launch("lock"))
        self.root.bind_all("<Control-Alt-n>", lambda e: self.launch("notes"))
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.particles = []
        self.draw_wallpaper()
        self.shortcuts = []
        self.create_shortcuts()
        self.seed_particles()
        self.animate_particles()
        self.welcome = None
        if self.config.get("show_welcome", True):
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
            target.write_text("Sandboxed VM\nMade by 2pro12342\n\nThis is a real Linux desktop running in a CodeHS sandbox.\n\nFirefox and Google Chrome are native applications. Files, Text Editor, Terminal and Calculator run as native Linux programs.\n\nRoblox opens the Roblox website. Roblox has no supported native Linux desktop client, so gameplay is not included.\n\nUse Start, the desktop shortcuts, or the taskbar to open apps. Drag title bars to move windows; minimize, maximize, and close use the native window manager. Alt+Tab switches windows.\n\nSave documents in this Documents folder. Use Settings > Create backup to create a ZIP in the CodeHS program directory. Download important work; CodeHS can recycle the running server.\n\nIf the runtime is reset, press Run again and allow the applications to reinstall.\n")

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
            elif action in ("firefox", "chrome", "roblox", "files", "terminal", "editor", "calculator", "settings", "about"):
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
            elif event[0] == "finished":
                self.refresh_welcome()
                print("DESKTOP READY — Sandboxed VM — Made by 2pro12342", flush=True)
        if not self.closed:
            self.root.after(150, self.pump)

    def draw_wallpaper(self):
        canvas = self.canvas
        canvas.delete("wallpaper")
        width = max(1, self.root.winfo_width())
        height = max(1, self.root.winfo_height())
        palette = {
            "Stark": ("#030405", "#080a0e", "#0c1016"),
            "Blue": ("#03070c", "#08111b", "#0d1824"),
            "Violet": ("#05040a", "#0e0b16", "#171121"),
            "Forest": ("#030807", "#08110f", "#0d1915"),
        }
        background, mid, accent = palette.get(self.config["wallpaper"], palette["Stark"])
        canvas.configure(bg=background)
        # Muted oversized geometry adds depth while keeping every option nearly black.
        canvas.create_oval(width * .39, -height * .78, width * 1.3, height * 1.05, fill=mid, outline="", tags="wallpaper")
        canvas.create_oval(width * .56, -height * .55, width * 1.35, height * 1.15, fill=accent, outline="", tags="wallpaper")
        canvas.create_oval(width * .72, -height * .28, width * 1.34, height * 1.02, fill=mid, outline="", tags="wallpaper")
        canvas.create_text(width * .63 + 3, height * .49 + 4, text="STARK", fill="#090b0e", font=("DejaVu Sans", max(42, min(92, int(width * .095))), "bold"), tags="wallpaper")
        canvas.create_text(width * .63, height * .49, text="STARK", fill="#191e26", font=("DejaVu Sans", max(42, min(92, int(width * .095))), "bold"), tags="wallpaper")
        canvas.create_line(width * .43, height * .60, width * .83, height * .60, fill="#252b34", width=1, tags="wallpaper")
        canvas.create_text(width * .63, height * .65, text="A DESKTOP THAT'S YOURS  /  " + AUTHOR, fill="#626c79", font=("DejaVu Sans", 9, "bold"), tags="wallpaper")
        canvas.create_text(34, height - 30, text="STARK  ·  DESKTOP ENVIRONMENT", fill="#626c79", font=("DejaVu Sans", 9, "bold"), anchor="w", tags="wallpaper")
        canvas.tag_lower("wallpaper")

    def seed_particles(self):
        self.canvas.delete("particle")
        self.particles = []
        width = max(1, self.root.winfo_width())
        height = max(1, self.root.winfo_height())
        for _ in range(max(10, int(self.config.get("particle_density", 70)))):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            radius = random.choice((1, 1, 1, 2))
            speed = random.uniform(0.5, 1.8) * float(self.config.get("particle_speed", 1.0))
            color = random.choice(("#323944", "#414a57", "#596372"))
            dot = self.canvas.create_oval(x, y, x + radius * 2, y + radius * 2, fill=color, outline="", tags="particle")
            self.particles.append((dot, x, y, radius, speed))

    def animate_particles(self):
        if self.closed:
            return
        height = max(1, self.root.winfo_height())
        updated = []
        for dot, x, y, radius, speed in self.particles:
            y -= speed
            x += math.sin((y + x) * 0.018) * 0.35
            if y < -radius * 2:
                y = height + random.uniform(2, 40)
                x = random.uniform(0, max(1, self.root.winfo_width()))
            self.canvas.coords(dot, x, y, x + radius * 2, y + radius * 2)
            updated.append((dot, x, y, radius, speed))
        self.particles = updated
        self.root.after(40, self.animate_particles)

    def draw_shortcut_icon(self, canvas, action):
        canvas.delete("all")
        canvas.configure(bg="#0b1427")
        # Give each crisp, hand-drawn logo the same subtle desktop tile.
        canvas.create_oval(7, 8, 57, 58, fill="#07101e", outline="")
        canvas.create_oval(5, 4, 57, 56, fill="#172a43", outline="#405979", width=1)
        canvas.create_oval(8, 7, 54, 53, outline="#263e5d", width=1)
        if action == "files":
            canvas.create_polygon(13, 20, 25, 20, 29, 24, 48, 24, 48, 43, 13, 43, fill="#e6a735", outline="#ffdc82", width=1)
            canvas.create_polygon(13, 25, 49, 25, 45, 43, 16, 43, fill="#ffd36e", outline="#ffe6a3", width=1)
            canvas.create_line(17, 29, 45, 29, fill="#fff2c8", width=2)
            canvas.create_line(17, 40, 43, 40, fill="#f2bd4e", width=1)
        elif action == "chrome":
            # Three clean color segments, with Google's white-ringed blue center.
            for color, start in (("#e94235", 30), ("#fbbc04", 150), ("#34a853", 270)):
                canvas.create_arc(11, 10, 51, 50, start=start, extent=120, style="pieslice", fill=color, outline=color)
            canvas.create_oval(21, 20, 41, 40, fill="#f7f9fc", outline="")
            canvas.create_oval(24, 23, 38, 37, fill="#4285f4", outline="#dceaff", width=1)
            canvas.create_oval(25, 24, 37, 36, outline="#76a9fa", width=1)
        elif action == "firefox":
            # Purple globe with the orange fox/flame sweeping around it.
            canvas.create_oval(14, 14, 48, 48, fill="#713fc4", outline="#a987f0", width=1)
            canvas.create_arc(17, 18, 46, 47, start=205, extent=245, style="arc", outline="#a98aff", width=3)
            canvas.create_polygon(15, 33, 11, 23, 19, 25, 24, 13, 29, 20, 40, 15, 38, 23, 50, 22, 44, 29, 48, 35, 40, 35, 36, 44, 28, 48, 20, 44, 16, 39, fill="#ff812e", outline="#ffb24d", width=1, smooth=True)
            canvas.create_polygon(17, 32, 26, 25, 38, 24, 34, 31, 27, 35, 22, 41, fill="#ffd45e", outline="", smooth=True)
            canvas.create_oval(23, 31, 40, 45, fill="#7045cf", outline="")
        elif action == "roblox":
            canvas.create_polygon(31, 10, 50, 15, 45, 45, 15, 50, 10, 20, fill="#f7f9fc", outline="#ffffff", width=1)
            canvas.create_polygon(30, 22, 39, 24, 37, 38, 22, 40, 20, 26, fill="#172a43", outline="")
        elif action == "terminal":
            canvas.create_rectangle(11, 13, 51, 47, fill="#091525", outline="#63a9ff", width=2)
            canvas.create_line(18, 22, 25, 29, 18, 36, fill="#eff6ff", width=3, capstyle="round", joinstyle="round")
            canvas.create_line(30, 37, 42, 37, fill="#69d3a0", width=3, capstyle="round")
            canvas.create_oval(44, 16, 47, 19, fill="#69d3a0", outline="")
        elif action == "settings":
            points = []
            for index in range(48):
                angle = math.pi * index / 24 - math.pi / 2
                radius = 19 if index % 6 in (0, 1, 2) else 15
                points.extend((31 + math.cos(angle) * radius, 30 + math.sin(angle) * radius))
            canvas.create_polygon(points, fill="#91b5e2", outline="#d5e5fa", width=1, smooth=True)
            canvas.create_oval(24, 23, 38, 37, fill="#172a43", outline="#e0edff", width=2)
        elif action == "editor":
            canvas.create_rectangle(16, 11, 45, 49, fill="#f5f8ff", outline="#a9c9f4", width=1)
            canvas.create_polygon(37, 11, 45, 19, 37, 19, fill="#c8dcf7", outline="")
            for y in (25, 31, 37):
                canvas.create_line(21, y, 39, y, fill="#6798d0", width=2)
            canvas.create_line(21, 43, 34, 43, fill="#6798d0", width=2)
        elif action == "calculator":
            canvas.create_rectangle(17, 10, 45, 50, fill="#263d5a", outline="#9dc5f3", width=2)
            canvas.create_rectangle(21, 15, 41, 23, fill="#d9ebff", outline="")
            for x, y in ((23, 29), (31, 29), (39, 29), (23, 37), (31, 37), (39, 37), (23, 45), (31, 45), (39, 45)):
                canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="#83b7ef" if (x, y) in ((39, 29), (39, 37), (39, 45)) else "#f0f6ff", outline="")
        factor = max(0.65, min(1.55, float(self.config.get("icon_size", 62)) / 62))
        canvas.scale("all", 31, 30, factor, factor)

    def create_shortcuts(self):
        entries = [
            ("center", "Stark Center"), ("files", "Files"), ("firefox", "Firefox"),
            ("chrome", "Google Chrome"), ("roblox", "Roblox (web)"),
            ("terminal", "Terminal"), ("editor", "Text Editor"),
            ("calculator", "Calculator"), ("settings", "Settings"), ("notes", "Notes")
        ]
        for action, label in entries:
            tile = tk.Frame(self.root, bg="#030405", cursor="hand2")
            icon_size = int(self.config.get("icon_size", 62))
            icon = tk.Canvas(tile, width=icon_size, height=icon_size, bg="#030405", highlightthickness=0, cursor="hand2")
            icon.pack()
            self.draw_shortcut_icon(icon, action)
            caption = tk.Label(tile, text=label, bg="#0b1427", fg="#e5efff", font=("DejaVu Sans", 9, "bold"), cursor="hand2")
            caption.pack(pady=(1, 0))
            for widget in (tile, icon, caption):
                widget.bind("<Button-1>", lambda _event, name=action: self.launch(name))
                widget.bind("<Enter>", lambda _event, item=tile, text=caption: (item.configure(bg="#172a43"), text.configure(bg="#172a43")))
                widget.bind("<Leave>", lambda _event, item=tile, text=caption: (item.configure(bg="#030405"), text.configure(bg="#030405")))
            self.shortcuts.append(tile)
        self.position_shortcuts()

    def position_shortcuts(self):
        icon_size = int(self.config.get("icon_size", 62))
        tile_height = icon_size + 28
        rows = max(1, (self.height - 64) // tile_height)
        for index, tile in enumerate(self.shortcuts):
            tile.place(x=14 + (index // rows) * (icon_size + 42), y=12 + (index % rows) * tile_height, width=icon_size + 26, height=tile_height)

    def make_window(self, title, width=600, height=440):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.configure(bg="#f5f8ff")
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
        self.welcome = self.make_window("Welcome to Sandboxed VM", 680, 480)
        self.welcome.configure(bg="#f4f7fc")
        header = tk.Frame(self.welcome, bg="#142944", padx=30, pady=24)
        header.pack(fill="x")
        tk.Label(header, text="Welcome to your desktop", bg="#142944", fg="#f2f7ff", font=("DejaVu Sans", 22, "bold"), anchor="w").pack(fill="x")
        tk.Label(header, text="A real Linux workspace, ready when you are.", bg="#142944", fg="#b7cce5", font=("DejaVu Sans", 11), anchor="w").pack(fill="x", pady=(5, 0))
        pane = tk.Frame(self.welcome, bg="#f4f7fc", padx=30, pady=20)
        pane.pack(fill="both", expand=True)
        tk.Label(pane, text="Getting things ready", bg="#f4f7fc", fg="#20344f", font=("DejaVu Sans", 12, "bold"), anchor="w").pack(fill="x", pady=(0, 10))
        self.status_vars = {}
        for app, label in (("desktop", "Desktop tools"), ("firefox", "Mozilla Firefox"), ("chrome", "Google Chrome")):
            row = tk.Frame(pane, bg="#ffffff", padx=14, pady=8, highlightthickness=1, highlightbackground="#e0e7f0")
            row.pack(fill="x", pady=3)
            tk.Label(row, text="●", bg="#ffffff", fg="#3d86c6", font=("DejaVu Sans", 10), width=2).pack(side="left")
            tk.Label(row, text=label, width=19, bg="#ffffff", fg="#263a55", font=("DejaVu Sans", 10, "bold"), anchor="w").pack(side="left")
            variable = tk.StringVar(value=self.status[app])
            self.status_vars[app] = variable
            tk.Label(row, textvariable=variable, bg="#ffffff", fg="#60748d", font=("DejaVu Sans", 10), anchor="w", wraplength=290).pack(side="left", fill="x", expand=True)
        tk.Label(pane, text="Quick launch", bg="#f4f7fc", fg="#20344f", font=("DejaVu Sans", 12, "bold"), anchor="w").pack(fill="x", pady=(14, 8))
        buttons = tk.Frame(pane, bg="#f4f7fc")
        buttons.pack(fill="x")
        for action, label, color in (("center", "Stark Center", "#245ba8"), ("firefox", "Open Firefox", "#245ba8"), ("chrome", "Open Chrome", "#245ba8"), ("files", "Browse files", "#e5edf7")):
            is_primary = color == "#245ba8"
            tk.Button(buttons, text=label, command=lambda name=action: self.launch(name), bg=color, fg="white" if is_primary else "#29415f", activebackground="#19457e" if is_primary else "#d5e2f1", activeforeground="white" if is_primary else "#20344f", relief="flat", padx=14, pady=9, cursor="hand2", font=("DejaVu Sans", 10, "bold" if is_primary else "normal")).pack(side="left", padx=(0, 9))
        tk.Label(pane, text="Tip: open Stark Center for search and workspace tools. Roblox opens the website; native gameplay isn't available on Linux.", bg="#f4f7fc", fg="#65788f", font=("DejaVu Sans", 9), justify="left", anchor="w", wraplength=610).pack(fill="x", pady=(14, 0))
        show_at_start = tk.BooleanVar(value=self.config.get("show_welcome", True))
        def set_welcome_preference():
            self.config["show_welcome"] = show_at_start.get()
            (BASE / "settings.json").write_text(json.dumps(self.config))
        tk.Checkbutton(pane, text="Show this setup window next time", variable=show_at_start, command=set_welcome_preference, bg="#f4f7fc", fg="#65788f", activebackground="#f4f7fc", selectcolor="#ffffff", font=("DejaVu Sans", 9)).pack(anchor="w", pady=(6, 0))

    def refresh_welcome(self):
        if self.welcome and self.welcome.winfo_exists():
            for app, variable in self.status_vars.items():
                variable.set(self.status[app])

    def notice(self, title, text):
        window = self.make_window(title, 620, 330)
        tk.Label(window, text=title, bg="#f5f8ff", fg="#162d4b", font=("DejaVu Sans", 17, "bold"), anchor="w").pack(fill="x", padx=24, pady=(22, 10))
        body = tk.Text(window, wrap="word", bg="#f5f8ff", fg="#314963", relief="flat", padx=24, pady=8, font=("DejaVu Sans", 10))
        body.pack(fill="both", expand=True)
        body.insert("1.0", text)
        body.configure(state="disabled")
        tk.Button(window, text="Close", command=window.destroy, padx=20, pady=7).pack(pady=14)

    def feature_hub(self):
        window = self.make_window("STARK CENTER", 760, 520)
        window.configure(bg="#080b10")
        top = tk.Frame(window, bg="#101720", padx=24, pady=18)
        top.pack(fill="x")
        tk.Label(top, text="STARK  /  CONTROL CENTER", bg="#101720", fg="#f1f5fa", font=("DejaVu Sans", 18, "bold")).pack(anchor="w")
        tk.Label(top, text="Apps, workspace tools, and quick actions  ·  Ctrl+Alt+Space", bg="#101720", fg="#8b9bad", font=("DejaVu Sans", 9)).pack(anchor="w", pady=(4, 12))
        search = tk.Entry(top, bg="#080c12", fg="#e9f1fb", insertbackground="white", relief="flat", font=("DejaVu Sans", 11))
        search.pack(fill="x", ipady=9)
        search.insert(0, "Search apps and tools…")
        body = tk.Frame(window, bg="#080b10", padx=22, pady=16)
        body.pack(fill="both", expand=True)
        tk.Label(body, text="QUICK LAUNCH", bg="#080b10", fg="#71869d", font=("DejaVu Sans", 8, "bold")).pack(anchor="w", pady=(0, 9))
        scroll = tk.Canvas(body, bg="#080b10", highlightthickness=0)
        bar = tk.Scrollbar(body, orient="vertical", command=scroll.yview)
        scroll.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        scroll.pack(side="left", fill="both", expand=True)
        grid = tk.Frame(scroll, bg="#080b10")
        grid_window = scroll.create_window((0, 0), window=grid, anchor="nw")
        grid.bind("<Configure>", lambda _e: scroll.configure(scrollregion=scroll.bbox("all")))
        scroll.bind("<Configure>", lambda event: scroll.itemconfigure(grid_window, width=event.width))
        entries = [
            ("files", "Files", "Browse Documents"), ("firefox", "Firefox", "Web browser"),
            ("chrome", "Chrome", "Web browser"), ("roblox", "Roblox", "Open website"),
            ("terminal", "Terminal", "Command line"), ("editor", "Text Editor", "Edit a document"),
            ("calculator", "Calculator", "Calculator"), ("notes", "Notes", "Autosaved workspace notes"),
            ("file_search", "Find files", "Search Documents"), ("recent", "Recent", "Recently opened items"),
            ("calendar", "Calendar", "Month at a glance"), ("clock", "World clock", "Local and UTC time"),
            ("clipboard", "Clipboard", "Recent copied text"), ("system_info", "System info", "Runtime details"),
            ("settings", "Personalize", "Wallpaper and motion"), ("backup", "Back up", "Save documents to ZIP"),
            ("restore", "Restore", "Extract a document backup"), ("export_settings", "Export settings", "Save preferences JSON"),
            ("import_settings", "Import settings", "Load preferences JSON"), ("custom_shortcut", "Add shortcut", "Create a quick-launch link"),
            ("lock", "Lock screen", "Hide the desktop"), ("window_switcher", "Windows", "Switch open windows"),
            ("trash", "Trash a file", "Move a document to Trash"), ("trash_viewer", "Trash folder", "Restore deleted files"),
            ("screenshot", "Screenshot", "Capture the desktop if supported"),
        ]
        entries.extend(("custom_url:" + item.get("url", ""), item.get("label", "Web shortcut"), item.get("url", "")) for item in self.config.get("custom_shortcuts", []))
        buttons = []
        for index, (action, label, detail) in enumerate(entries):
            card = tk.Frame(grid, bg="#101720", padx=12, pady=10, highlightthickness=1, highlightbackground="#1c2938")
            card.grid(row=index // 3, column=index % 3, sticky="nsew", padx=5, pady=5)
            button = tk.Button(card, text=label, command=lambda name=action: self.launch(name), anchor="w", bg="#101720", fg="#eaf2fc", activebackground="#192637", activeforeground="white", relief="flat", font=("DejaVu Sans", 10, "bold"), cursor="hand2")
            button.pack(fill="x")
            tk.Label(card, text=detail, bg="#101720", fg="#8293a8", anchor="w", font=("DejaVu Sans", 8)).pack(fill="x", pady=(3, 0))
            buttons.append((card, (label + " " + detail + " " + action).lower()))
        for column in range(3):
            grid.grid_columnconfigure(column, weight=1)
        grid.grid_rowconfigure(7, weight=1)
        def filter_entries(_event=None):
            query = search.get().strip().lower()
            if query == "search apps and tools…":
                query = ""
            for card, text in buttons:
                if query in text:
                    card.grid()
                else:
                    card.grid_remove()
        search.bind("<KeyRelease>", filter_entries)
        search.bind("<FocusIn>", lambda _e: search.delete(0, "end") if search.get() == "Search apps and tools…" else None)

    def notes_app(self):
        path = DOCUMENTS / "Notes.txt"
        window = self.make_window("Notes — autosaved", 620, 440)
        window.configure(bg="#090d13")
        tk.Label(window, text="NOTES  /  autosaves to Documents", bg="#111923", fg="#eaf2fb", padx=16, pady=12, anchor="w", font=("DejaVu Sans", 11, "bold")).pack(fill="x")
        editor = tk.Text(window, wrap="word", bg="#0a0f16", fg="#d9e4f0", insertbackground="white", selectbackground="#274668", relief="flat", padx=18, pady=16, font=("DejaVu Sans Mono", 10))
        editor.pack(fill="both", expand=True, padx=10, pady=10)
        try:
            editor.insert("1.0", path.read_text(errors="replace"))
        except OSError:
            pass
        def save(_event=None):
            try:
                path.write_text(editor.get("1.0", "end-1c"))
            except OSError as error:
                self.notify("Notes could not save: " + str(error))
        editor.bind("<KeyRelease>", save)
        window.protocol("WM_DELETE_WINDOW", lambda: (save(), window.destroy()))

    def file_search(self):
        window = self.make_window("Find files", 620, 430)
        window.configure(bg="#090d13")
        tk.Label(window, text="SEARCH DOCUMENTS", bg="#111923", fg="#eaf2fb", padx=16, pady=12, anchor="w", font=("DejaVu Sans", 11, "bold")).pack(fill="x")
        query = tk.Entry(window, bg="#080c12", fg="white", insertbackground="white", relief="flat", font=("DejaVu Sans", 11))
        query.pack(fill="x", padx=16, pady=12, ipady=8)
        listing = tk.Listbox(window, bg="#0b1119", fg="#dce7f5", selectbackground="#1f4b70", relief="flat", font=("DejaVu Sans", 10))
        listing.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        matches = []
        def scan(_event=None):
            listing.delete(0, "end")
            matches.clear()
            term = query.get().strip().lower()
            for path in DOCUMENTS.rglob("*"):
                if path.is_file() and term in path.name.lower():
                    matches.append(path)
                    listing.insert("end", str(path.relative_to(DOCUMENTS)))
        def open_match(_event=None):
            selection = listing.curselection()
            if selection:
                self.open_document(matches[selection[0]])
        query.bind("<KeyRelease>", scan)
        listing.bind("<Double-Button-1>", open_match)
        scan()

    def open_document(self, path):
        path = Path(path)
        if path.is_file():
            self.record_recent(path)
            if path.suffix.lower() in (".txt", ".md", ".py", ".html", ".json", ".csv", ".log"):
                window = self.make_window(path.name, 650, 460)
                window.configure(bg="#090d13")
                view = tk.Text(window, wrap="word", bg="#0a0f16", fg="#d9e4f0", insertbackground="white", relief="flat", padx=18, pady=16, font=("DejaVu Sans Mono", 10))
                view.pack(fill="both", expand=True)
                try:
                    view.insert("1.0", path.read_text(errors="replace"))
                except OSError as error:
                    view.insert("1.0", str(error))
                view.configure(state="disabled")
            else:
                self.notify("Preview supports text files. File: " + path.name)

    def record_recent(self, path):
        recent_path = BASE / "recent.json"
        try:
            items = json.loads(recent_path.read_text())
        except (OSError, ValueError):
            items = []
        value = str(path)
        items = [value] + [item for item in items if item != value]
        recent_path.write_text(json.dumps(items[:30]))

    def recent_files(self):
        try:
            items = json.loads((BASE / "recent.json").read_text())
        except (OSError, ValueError):
            items = []
        window = self.make_window("Recent items", 520, 380)
        window.configure(bg="#090d13")
        tk.Label(window, text="RECENTLY OPENED", bg="#111923", fg="#eaf2fb", padx=16, pady=12, anchor="w", font=("DejaVu Sans", 11, "bold")).pack(fill="x")
        listing = tk.Listbox(window, bg="#0b1119", fg="#dce7f5", selectbackground="#1f4b70", relief="flat")
        listing.pack(fill="both", expand=True, padx=16, pady=16)
        valid = [Path(item) for item in items if Path(item).is_file()]
        for item in valid:
            listing.insert("end", item.name + "  —  " + str(item.parent))
        listing.bind("<Double-Button-1>", lambda _e: self.open_document(valid[listing.curselection()[0]]) if listing.curselection() else None)

    def calendar_app(self):
        today = datetime.date.today()
        window = self.make_window("Calendar", 420, 360)
        window.configure(bg="#090d13")
        tk.Label(window, text=today.strftime("%B %Y").upper(), bg="#111923", fg="#eaf2fb", padx=18, pady=16, font=("DejaVu Sans", 16, "bold")).pack(fill="x")
        tk.Label(window, text=calendar.month(today.year, today.month), bg="#090d13", fg="#a9c5df", justify="left", font=("DejaVu Sans Mono", 13), padx=30, pady=24).pack(anchor="w")
        tk.Label(window, text="Today: " + today.strftime("%A, %B %d, %Y"), bg="#090d13", fg="#dce7f5", padx=30).pack(anchor="w")

    def clock_app(self):
        window = self.make_window("World clock", 400, 240)
        window.configure(bg="#090d13")
        tk.Label(window, text="TIME", bg="#111923", fg="#eaf2fb", padx=18, pady=14, anchor="w", font=("DejaVu Sans", 12, "bold")).pack(fill="x")
        local = tk.Label(window, bg="#090d13", fg="#f2f6fc", font=("DejaVu Sans", 22, "bold"), pady=18)
        local.pack()
        utc = tk.Label(window, bg="#090d13", fg="#829ab2", font=("DejaVu Sans", 11))
        utc.pack()
        def tick():
            if not window.winfo_exists():
                return
            now = datetime.datetime.now()
            local.configure(text=now.strftime("%H:%M:%S") + "  ·  Local")
            utc.configure(text=datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S  ·  UTC"))
            window.after(1000, tick)
        tick()

    def system_info(self):
        info = "STARK VM  /  SYSTEM INFORMATION\n\n" + "Platform: {}\nPython: {}\nScreen: {} × {}\nDocuments: {}\nDesktop status: {}\nFirefox: {}\nChrome: {}\n\nThis is a Linux desktop session running inside a sandbox, not a separate Windows installation.".format(platform.platform(), platform.python_version(), self.width, self.height, DOCUMENTS, self.status.get("desktop"), self.status.get("firefox"), self.status.get("chrome"))
        self.notice("System information", info)

    def clipboard_app(self):
        try:
            text = self.root.clipboard_get().strip()
            history = getattr(self, "clipboard_history", [])
            if text and (not history or history[0] != text):
                history.insert(0, text[:1200])
                self.clipboard_history = history[:20]
        except tk.TclError:
            pass
        items = getattr(self, "clipboard_history", [])
        window = self.make_window("Clipboard history", 540, 360)
        window.configure(bg="#090d13")
        tk.Label(window, text="RECENT CLIPBOARD TEXT  ·  stored for this session", bg="#111923", fg="#eaf2fb", padx=16, pady=12, anchor="w", font=("DejaVu Sans", 10, "bold")).pack(fill="x")
        listing = tk.Listbox(window, bg="#0b1119", fg="#dce7f5", selectbackground="#1f4b70", relief="flat")
        listing.pack(fill="both", expand=True, padx=16, pady=16)
        for item in items:
            listing.insert("end", item.replace("\\n", " ")[:100])
        def copy_back(_event=None):
            if listing.curselection():
                self.root.clipboard_clear()
                self.root.clipboard_append(items[listing.curselection()[0]])
        listing.bind("<Double-Button-1>", copy_back)

    def notify(self, text):
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.configure(bg="#172535")
        popup.geometry("360x82+{}+{}".format(max(10, self.width - 380), max(10, self.height - 110)))
        tk.Label(popup, text="STARK  ·  NOTIFICATION", bg="#172535", fg="#8cb9e2", font=("DejaVu Sans", 8, "bold"), anchor="w", padx=14, pady=8).pack(fill="x")
        tk.Label(popup, text=text, bg="#172535", fg="#f0f5fb", wraplength=330, justify="left", anchor="w", padx=14).pack(fill="x")
        popup.after(3500, popup.destroy)

    def lock_screen(self):
        overlay = tk.Toplevel(self.root)
        overlay.title("Locked — Sandboxed VM")
        overlay.configure(bg="#05070a")
        overlay.geometry("{}x{}+0+0".format(self.width, self.height))
        overlay.transient(self.root)
        overlay.grab_set()
        tk.Label(overlay, text="STARK", bg="#05070a", fg="#dce5f0", font=("DejaVu Sans", 38, "bold")).pack(pady=(self.height // 4, 8))
        tk.Label(overlay, text=datetime.datetime.now().strftime("%A  ·  %H:%M"), bg="#05070a", fg="#8294a8", font=("DejaVu Sans", 12)).pack(pady=(0, 24))
        tk.Button(overlay, text="Unlock desktop", command=overlay.destroy, bg="#172535", fg="white", relief="flat", padx=20, pady=10).pack()
        overlay.bind("<Escape>", lambda _e: overlay.destroy())

    def window_switcher(self):
        windows = [child for child in self.root.winfo_children() if isinstance(child, tk.Toplevel) and child.winfo_exists()]
        if not windows:
            self.notify("No open windows")
            return
        window = self.make_window("Open windows", 440, 340)
        window.configure(bg="#090d13")
        listing = tk.Listbox(window, bg="#0b1119", fg="#dce7f5", selectbackground="#1f4b70", relief="flat")
        listing.pack(fill="both", expand=True, padx=16, pady=16)
        for child in windows:
            listing.insert("end", child.title())
        def raise_window(_event=None):
            if listing.curselection():
                windows[listing.curselection()[0]].deiconify()
                windows[listing.curselection()[0]].lift()
                window.destroy()
        listing.bind("<Double-Button-1>", raise_window)

    def trash_viewer(self):
        trash = HERE / "Trash"
        trash.mkdir(exist_ok=True)
        window = self.make_window("Trash", 520, 380)
        window.configure(bg="#090d13")
        tk.Label(window, text="TRASH  /  restore or permanently delete", bg="#111923", fg="#eaf2fb", padx=16, pady=12, anchor="w", font=("DejaVu Sans", 10, "bold")).pack(fill="x")
        listing = tk.Listbox(window, bg="#0b1119", fg="#dce7f5", selectbackground="#1f4b70", relief="flat")
        listing.pack(fill="both", expand=True, padx=16, pady=12)
        def refresh():
            listing.delete(0, "end")
            for item in sorted(trash.iterdir()):
                listing.insert("end", item.name)
        actions = tk.Frame(window, bg="#090d13")
        actions.pack(fill="x", padx=16, pady=(0, 14))
        def restore():
            selected = listing.curselection()
            if not selected:
                return
            source = trash / listing.get(selected[0])
            target = DOCUMENTS / source.name
            if target.exists():
                target = DOCUMENTS / (source.stem + "_restored" + source.suffix)
            shutil.move(str(source), str(target))
            refresh()
        def delete_permanently():
            selected = listing.curselection()
            if selected:
                target = trash / listing.get(selected[0])
                target.unlink(missing_ok=True)
                refresh()
        tk.Button(actions, text="Restore to Documents", command=restore, bg="#245ba8", fg="white", relief="flat", padx=10, pady=7).pack(side="left", padx=(0, 8))
        tk.Button(actions, text="Delete permanently", command=delete_permanently, bg="#192433", fg="#e5edf7", relief="flat", padx=10, pady=7).pack(side="left")
        refresh()

    def file_trash(self):
        path = filedialog.askopenfilename(initialdir=str(DOCUMENTS), title="Choose a document to move to Trash")
        if not path:
            return
        trash = HERE / "Trash"
        trash.mkdir(exist_ok=True)
        source = Path(path)
        target = trash / source.name
        counter = 1
        while target.exists():
            target = trash / (source.stem + "_{}".format(counter) + source.suffix)
            counter += 1
        shutil.move(str(source), str(target))
        self.notify("Moved to Trash: " + target.name)

    def save_settings_file(self, importing=False):
        if importing:
            path = filedialog.askopenfilename(title="Import settings", filetypes=[("JSON settings", "*.json")])
            if path:
                try:
                    values = json.loads(Path(path).read_text())
                    if not isinstance(values, dict):
                        raise ValueError("Settings file must contain a JSON object")
                    self.config.update(values)
                    (BASE / "settings.json").write_text(json.dumps(self.config))
                    self.draw_wallpaper()
                    self.seed_particles()
                    self.notify("Settings imported")
                except (OSError, ValueError) as error:
                    self.notice("Import failed", str(error))
        else:
            path = filedialog.asksaveasfilename(title="Export settings", defaultextension=".json", filetypes=[("JSON settings", "*.json")])
            if path:
                Path(path).write_text(json.dumps(self.config, indent=2))
                self.notify("Settings exported")

    def restore_backup(self):
        path = filedialog.askopenfilename(title="Choose a document backup", filetypes=[("ZIP backup", "*.zip")])
        if not path:
            return
        try:
            import zipfile
            with zipfile.ZipFile(path) as archive:
                root = DOCUMENTS.resolve()
                names = archive.namelist()
                for name in names:
                    target = (DOCUMENTS / name).resolve()
                    if os.path.commonpath((str(root), str(target))) != str(root):
                        raise ValueError("Backup contains an unsafe path")
                archive.extractall(DOCUMENTS)
                nested = DOCUMENTS / "Documents"
                if nested.is_dir():
                    for child in nested.iterdir():
                        destination = DOCUMENTS / child.name
                        if not destination.exists():
                            shutil.move(str(child), str(destination))
                    nested.rmdir()
            self.notify("Backup restored to Documents")
        except (OSError, ValueError) as error:
            self.notice("Restore failed", str(error))

    def add_custom_shortcut(self):
        label = simpledialog.askstring("New shortcut", "Shortcut name:")
        if not label:
            return
        url = simpledialog.askstring("New shortcut", "Website URL (https://…) :")
        if not url or not url.startswith(("https://", "http://")):
            self.notify("Enter a valid http:// or https:// address")
            return
        shortcuts = self.config.setdefault("custom_shortcuts", [])
        shortcuts.append({"label": label[:40], "url": url})
        (BASE / "settings.json").write_text(json.dumps(self.config))
        self.notify("Shortcut saved. Open Stark Center to find it.")

    def capture_screenshot(self):
        target = filedialog.asksaveasfilename(title="Save desktop screenshot", defaultextension=".png", filetypes=[("PNG image", "*.png")])
        if not target:
            return
        try:
            result = subprocess.run(["import", "-window", "root", target], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15)
            if result.returncode:
                raise RuntimeError(result.stderr.decode(errors="replace")[-500:] or "Image capture utility is unavailable")
            self.notify("Screenshot saved")
        except (OSError, subprocess.SubprocessError, RuntimeError) as error:
            self.notice("Screenshot unavailable", "This runtime does not provide a desktop capture utility. " + str(error))

    def launch(self, action):
        if action.startswith("custom_url:"):
            url = action[len("custom_url:"):]
            browser = self.config.get("browser", "Firefox").lower()
            custom_profile = BASE / "profiles/custom"
            custom_profile.mkdir(parents=True, exist_ok=True)
            if browser == "chrome" and self.status.get("chrome") == "Installed":
                self.spawn("chrome", [str(APPS / "chrome/opt/google/chrome/google-chrome"), "--user-data-dir=" + str(custom_profile), "--disable-dev-shm-usage", "--no-default-browser-check", url])
            elif self.status.get("firefox") == "Installed":
                self.spawn("firefox", [str(APPS / "firefox/firefox"), "--profile", str(custom_profile), url])
            else:
                self.show_welcome()
            return
        tool_actions = {
            "center": self.feature_hub, "notes": self.notes_app, "file_search": self.file_search,
            "recent": self.recent_files, "calendar": self.calendar_app, "clock": self.clock_app,
            "clipboard": self.clipboard_app, "system_info": self.system_info,
            "lock": self.lock_screen, "window_switcher": self.window_switcher,
            "trash": self.file_trash, "trash_viewer": self.trash_viewer, "restore": self.restore_backup,
            "export_settings": lambda: self.save_settings_file(False),
            "import_settings": lambda: self.save_settings_file(True),
            "custom_shortcut": self.add_custom_shortcut, "screenshot": self.capture_screenshot,
        }
        if action in tool_actions:
            tool_actions[action]()
            return
        if action == "backup":
            self.backup()
            return
        if action == "stop":
            self.close()
            return
        if action == "about":
            self.notice("About Sandboxed VM", "Sandboxed VM\nMade by 2pro12342\n\nA real Linux desktop session inside CodeHS.\n\nWindow manager: JWM\nFile manager: PCManFM\nTerminal: xterm\nText editor: Mousepad\nCalculator: Galculator\nBrowsers: Firefox and Google Chrome\n\nRoblox is a website shortcut. Native Roblox gameplay is not supported on Linux.\n\nThis project is a Linux sandbox desktop, not a Microsoft Windows installation.")
            return
        if action == "settings":
            self.settings()
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
        if action == "editor":
            self.record_recent(DOCUMENTS / "Welcome to Sandboxed VM.txt")
        try:
            process = self.spawn(name, args)
            self.root.lower()
            self.root.after(2400, lambda: self.check_launch(name, process))
        except OSError as exc:
            self.notice("Could not open " + action, str(exc))

    def check_launch(self, name, process):
        result = process.poll()
        if result is not None and result != 0:
            log = (LOGS / (name + ".log")).read_text(errors="replace")[-1800:]
            self.failures[name] = log
            print("LAUNCH ERROR:", name, log, flush=True)
            self.notice("Could not open " + name, "The real application exited with code {}.\n\n{}".format(result, log))

    def settings(self):
        window = self.make_window("Settings — Sandboxed VM", 620, 500)
        window.configure(bg="#090d13")
        header = tk.Frame(window, bg="#101720", padx=24, pady=18)
        header.pack(fill="x")
        tk.Label(header, text="Personalize your desktop", bg="#101720", fg="#f2f7ff", font=("DejaVu Sans", 17, "bold")).pack(anchor="w")
        tk.Label(header, text="Tune the Stark look, motion, and browser preference.", bg="#101720", fg="#91a4b9", font=("DejaVu Sans", 10)).pack(anchor="w", pady=(3, 0))
        frame = tk.Frame(window, bg="#090d13", padx=24, pady=18)
        frame.pack(fill="both", expand=True)
        options = tk.Frame(frame, bg="#101720", padx=16, pady=13, highlightthickness=1, highlightbackground="#1c2938")
        options.pack(fill="x")
        tk.Label(options, text="APPEARANCE  /  MOTION", bg="#101720", fg="#8298ae", font=("DejaVu Sans", 8, "bold")).pack(anchor="w", pady=(0, 8))
        tk.Label(options, text="Wallpaper", bg="#101720", fg="#e1eaf4", font=("DejaVu Sans", 10, "bold")).pack(anchor="w")
        wallpaper = tk.StringVar(value=self.config["wallpaper"])
        wallpaper_menu = tk.OptionMenu(options, wallpaper, "Stark", "Blue", "Violet", "Forest")
        wallpaper_menu.configure(bg="#192433", fg="#eaf2fc", activebackground="#25364a", relief="flat", highlightthickness=0, padx=8)
        wallpaper_menu["menu"].configure(bg="#101720", fg="#eaf2fc")
        wallpaper_menu.pack(anchor="w", pady=(3, 8))
        tk.Label(options, text="Browser for the Roblox website shortcut", bg="#101720", fg="#e1eaf4", font=("DejaVu Sans", 10, "bold")).pack(anchor="w")
        browser = tk.StringVar(value=self.config["browser"])
        browser_menu = tk.OptionMenu(options, browser, "Firefox", "Chrome")
        browser_menu.configure(bg="#192433", fg="#eaf2fc", activebackground="#25364a", relief="flat", highlightthickness=0, padx=8)
        browser_menu["menu"].configure(bg="#101720", fg="#eaf2fc")
        browser_menu.pack(anchor="w", pady=(3, 0))
        density = tk.IntVar(value=int(self.config.get("particle_density", 70)))
        speed = tk.DoubleVar(value=float(self.config.get("particle_speed", 1.0)))
        icon_scale = tk.IntVar(value=int(self.config.get("icon_size", 62)))
        tk.Label(options, text="Particle density", bg="#101720", fg="#e1eaf4", font=("DejaVu Sans", 10, "bold")).pack(anchor="w", pady=(10, 0))
        tk.Scale(options, from_=10, to=180, orient="horizontal", variable=density, bg="#101720", fg="#dce7f5", troughcolor="#080c12", highlightthickness=0, activebackground="#61a9e8", length=300).pack(anchor="w")
        tk.Label(options, text="Particle speed", bg="#101720", fg="#e1eaf4", font=("DejaVu Sans", 10, "bold")).pack(anchor="w")
        tk.Scale(options, from_=0.2, to=3.0, resolution=0.1, orient="horizontal", variable=speed, bg="#101720", fg="#dce7f5", troughcolor="#080c12", highlightthickness=0, activebackground="#61a9e8", length=220, showvalue=False).pack(anchor="w")
        tk.Label(options, text="Desktop icon size", bg="#101720", fg="#e1eaf4", font=("DejaVu Sans", 10, "bold")).pack(anchor="w")
        tk.Scale(options, from_=42, to=90, orient="horizontal", variable=icon_scale, bg="#101720", fg="#dce7f5", troughcolor="#080c12", highlightthickness=0, activebackground="#61a9e8", length=220, showvalue=False).pack(anchor="w")
        def save():
            self.config.update(wallpaper=wallpaper.get(), browser=browser.get(), particle_density=density.get(), particle_speed=speed.get(), icon_size=icon_scale.get())
            (BASE / "settings.json").write_text(json.dumps(self.config))
            self.draw_wallpaper()
            self.seed_particles()
            for tile in self.shortcuts:
                tile.destroy()
            self.shortcuts = []
            self.create_shortcuts()
            window.destroy()
        row = tk.Frame(frame, bg="#090d13")
        row.pack(anchor="w", pady=(14, 0))
        tk.Button(row, text="Save changes", command=save, bg="#245ba8", fg="white", activebackground="#19457e", activeforeground="white", relief="flat", padx=14, pady=8, cursor="hand2", font=("DejaVu Sans", 10, "bold")).pack(side="left", padx=(0, 8))
        tk.Button(row, text="Backup", command=self.backup, bg="#192433", fg="#dce7f5", activebackground="#25364a", relief="flat", padx=10, pady=8, cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(row, text="Restore", command=self.restore_backup, bg="#192433", fg="#dce7f5", activebackground="#25364a", relief="flat", padx=10, pady=8, cursor="hand2").pack(side="left")

    def backup(self):
        import zipfile
        output = HERE / "Sandboxed-VM-Documents.zip"
        with zipfile.ZipFile(str(output), "w", zipfile.ZIP_DEFLATED) as archive:
            for filename in DOCUMENTS.rglob("*"):
                if filename.is_file() and not filename.is_symlink():
                    archive.write(str(filename), str(filename.relative_to(DOCUMENTS)))
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
