"""Listen on my phone - serve the Narration folder over the local WiFi, with a
QR code. No accounts, no cloud; the files never leave your network. A random
token in the URL keeps other devices from browsing without scanning the code.
"""

import html
import http.server
import mimetypes
import os
import secrets
import socket
import threading
import urllib.parse

mimetypes.add_type("audio/mp4", ".m4a")
mimetypes.add_type("audio/mpeg", ".mp3")

AUDIO_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")


def local_ips():
    """All this PC's IPv4 addresses, best LAN guess first. A VPN can add an
    address your phone can't reach, so we rank real home-LAN ranges first and
    let the user pick if the default doesn't work."""
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        for res in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(res[4][0])
    except Exception:
        pass
    cand = [ip for ip in ips
            if not ip.startswith("127.") and not ip.startswith("169.254.")]

    def rank(ip):
        if ip.startswith("192.168."):
            return 0
        if ip.startswith("10."):
            return 1
        if ip.startswith("172."):
            try:
                o = int(ip.split(".")[1])
                if 16 <= o <= 31:
                    return 2
            except Exception:
                pass
        return 3
    return sorted(set(cand), key=rank) or ["127.0.0.1"]


def lan_ip():
    return local_ips()[0]


def _make_handler(folder, token):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            path = urllib.parse.unquote(self.path.split("?")[0])
            prefix = "/" + token
            if not path.startswith(prefix):
                self.send_error(404)
                return
            rest = path[len(prefix):]
            if rest in ("", "/"):
                self._index()
            elif rest.startswith("/f/"):
                self._file(rest[3:])
            else:
                self.send_error(404)

        def _index(self):
            try:
                files = sorted(f for f in os.listdir(folder)
                               if f.lower().endswith(AUDIO_EXT)
                               and os.path.isfile(os.path.join(folder, f)))
            except Exception:
                files = []
            rows = []
            for f in files:
                u = "/" + token + "/f/" + urllib.parse.quote(f)
                rows.append(
                    "<div class=item><div class=name>{n}</div>"
                    "<audio controls preload=none src='{u}'></audio>"
                    "<a class=dl href='{u}' download>Download</a></div>".format(
                        n=html.escape(f), u=u))
            body = "".join(rows) or "<p>No audio yet - convert something first.</p>"
            page = (
                "<!doctype html><html><head><meta charset=utf-8>"
                "<meta name=viewport content='width=device-width,initial-scale=1'>"
                "<title>EchoQuill - Listen</title><style>"
                "body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;"
                "background:#111;color:#eee;margin:0;padding:16px}"
                "h1{font-size:20px}.item{background:#1e1e22;border-radius:10px;"
                "padding:12px;margin:10px 0}.name{font-weight:600;margin-bottom:8px;"
                "word-break:break-word}audio{width:100%}"
                ".dl{display:inline-block;margin-top:8px;color:#4aa3ff;"
                "text-decoration:none}</style></head><body>"
                "<h1>\U0001f3a7 EchoQuill narrations</h1>" + body +
                "</body></html>")
            data = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _file(self, name):
            safe = os.path.basename(urllib.parse.unquote(name))
            fp = os.path.join(folder, safe)
            if not os.path.isfile(fp):
                self.send_error(404)
                return
            size = os.path.getsize(fp)
            ctype = mimetypes.guess_type(fp)[0] or "application/octet-stream"
            rng = self.headers.get("Range")
            start, end, status = 0, size - 1, 200
            if rng and rng.startswith("bytes="):
                try:
                    a, b = rng[6:].split("-")
                    start = int(a) if a else 0
                    end = int(b) if b else size - 1
                    end = min(end, size - 1)
                    status = 206
                except Exception:
                    start, end, status = 0, size - 1, 200
            length = end - start + 1
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            try:
                with open(fp, "rb") as fh:
                    fh.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = fh.read(min(65536, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            except Exception:
                pass
    return H


class PhoneShare:
    def __init__(self, folder):
        self.folder = folder
        self.token = secrets.token_urlsafe(6)
        self.httpd = None
        self.thread = None
        self.port = None

    def start(self):
        handler = _make_handler(self.folder, self.token)
        self.httpd = http.server.ThreadingHTTPServer(("0.0.0.0", 0), handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever,
                                       daemon=True)
        self.thread.start()

    def url_for(self, ip):
        return f"http://{ip}:{self.port}/{self.token}/"

    def url(self):
        return self.url_for(lan_ip())

    def stop(self):
        try:
            if self.httpd:
                self.httpd.shutdown()
                self.httpd.server_close()
        except Exception:
            pass


def open_phone_window(parent, cfg):
    """Start the share and pop a window with a QR code + link. Includes an IP
    picker in case a VPN/virtual adapter provides an address the phone can't
    reach."""
    import tkinter as tk
    from tkinter import ttk, messagebox
    from . import theme
    from .media_gui import narration_dir

    folder = narration_dir(cfg)
    share = PhoneShare(folder)
    try:
        share.start()
    except Exception as e:
        messagebox.showerror("Listen on my phone",
                             f"Could not start sharing: {e}", parent=parent)
        return

    ips = local_ips()
    state = {"ip": ips[0]}

    win = tk.Toplevel(parent)
    win.title("Listen on my phone")
    win.geometry("400x560")
    win.resizable(False, False)
    win.attributes("-topmost", True)
    theme.apply(win)

    def _close():
        share.stop()
        win.destroy()
    win.protocol("WM_DELETE_WINDOW", _close)

    ttk.Label(win, text="Listen on my phone", style="Title.TLabel").pack(
        anchor="w", padx=18, pady=(14, 2))
    ttk.Label(win, style="Dim.TLabel", wraplength=360, text=(
        "On your phone (SAME WiFi), scan this with the camera - or type the "
        "link below into the phone's browser. Tap a file to play or download. "
        "Nothing leaves your network.")).pack(anchor="w", padx=18)

    holder = tk.Label(win, bg=theme.PANEL)
    holder.pack(pady=10)
    urow = ttk.Frame(win)
    urow.pack(fill="x", padx=18)
    ent = ttk.Entry(urow)
    ent.pack(side="left", fill="x", expand=True, ipady=3)

    def _refresh():
        url = share.url_for(state["ip"])
        ent.configure(state="normal")
        ent.delete(0, "end"); ent.insert(0, url)
        ent.configure(state="readonly")
        try:
            import qrcode
            from PIL import ImageTk
            img = qrcode.make(url).resize((240, 240))
            photo = ImageTk.PhotoImage(img)
            holder.configure(image=photo)
            holder.image = photo
        except Exception:
            holder.configure(text="(QR unavailable - use the link below)",
                             fg=theme.FG)

    def _copy():
        try:
            import pyperclip
            pyperclip.copy(share.url_for(state["ip"]))
            _status.configure(text="Link copied ✓")
        except Exception:
            _status.configure(text="Copy failed")
    ttk.Button(urow, text="Copy link", command=_copy).pack(side="left", padx=(8, 0))

    if len(ips) > 1:
        prow = ttk.Frame(win)
        prow.pack(fill="x", padx=18, pady=(8, 0))
        ttk.Label(prow, text="If it won't load, try another address:",
                  style="Dim.TLabel").pack(side="left")
        ipvar = tk.StringVar(value=ips[0])

        def _pick(v):
            state["ip"] = v
            _refresh()
        ttk.OptionMenu(prow, ipvar, ips[0], *ips,
                       command=_pick).pack(side="left", padx=(6, 0))

    _status = ttk.Label(win, text="", style="Dim.TLabel")
    _status.pack(anchor="w", padx=18, pady=(4, 0))
    ttk.Label(win, style="Dim.TLabel", wraplength=360, text=(
        "Not loading? Two usual causes:\n"
        "- Firewall: the first time, Windows should ask to allow EchoQuill - "
        "say YES for Private networks. If you missed it, allow python/EchoQuill "
        "in Windows Defender Firewall (Private).\n"
        "- VPN: if you're on a VPN, your phone can't reach the VPN address - "
        "use the picker above to choose a 192.168.x address, or turn the VPN "
        "off briefly.\n\n"
        "Keep this window open while you listen; close it to stop sharing."
        )).pack(anchor="w", padx=18, pady=(8, 0))
    ttk.Button(win, text="Stop sharing", command=_close).pack(pady=12)

    _refresh()
    return win
