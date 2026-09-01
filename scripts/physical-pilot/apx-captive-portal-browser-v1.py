#!/usr/bin/env python3
"""Single-purpose ephemeral captive-portal window for the active APX Environment."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit


MAX_URL = 2048
CHECK_CLIENT = "/run/apx/host-services-client-v3.py"


def validated_url(value: str) -> str:
    if not value or len(value) > MAX_URL or any(ord(character) < 32 for character in value):
        raise ValueError("invalid portal URL")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname \
            or parsed.username is not None or parsed.password is not None:
        raise ValueError("invalid portal URL")
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("invalid portal URL") from error
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("invalid portal URL")
    return value


def portal_from_stdin() -> str:
    value = sys.stdin.readline(MAX_URL + 2)
    if not value.endswith("\n") or sys.stdin.read(1):
        raise ValueError("portal input differs")
    return validated_url(value[:-1])


def recheck() -> None:
    subprocess.run((CHECK_CLIENT, "wifi-connectivity-check"), stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12, check=False,
                   env={"PATH": "/usr/bin", "LC_ALL": "C"})


def main() -> int:
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000"))
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock = os.open(runtime / "apx-captive-portal-browser-v1.lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 4
    portal = portal_from_stdin()
    with tempfile.TemporaryDirectory(prefix="apx-captive-portal-", dir=runtime) as temporary:
        os.chmod(temporary, 0o700)
        os.environ["XDG_CACHE_HOME"] = temporary + "/cache"
        os.environ["XDG_CONFIG_HOME"] = temporary + "/config"
        os.environ["XDG_DATA_HOME"] = temporary + "/data"

        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("WebKit2", "4.1")
        from gi.repository import Gtk, WebKit2

        window = Gtk.Window(title="APX · AUTENTICAÇÃO WI-FI")
        window.set_default_size(960, 720)
        window.set_position(Gtk.WindowPosition.CENTER)
        window.connect("destroy", Gtk.main_quit)

        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        banner.set_border_width(10)
        label = Gtk.Label(label="APX WI-FI · JANELA TEMPORÁRIA · OS DADOS SERÃO APAGADOS AO FECHAR")
        label.set_xalign(0)
        close = Gtk.Button(label="FECHAR E VERIFICAR")
        close.connect("clicked", lambda _button: window.destroy())
        banner.pack_start(label, True, True, 0)
        banner.pack_end(close, False, False, 0)
        layout.pack_start(banner, False, False, 0)

        manager = WebKit2.WebsiteDataManager.new_ephemeral()
        context = WebKit2.WebContext.new_with_website_data_manager(manager)
        context.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)
        web = WebKit2.WebView.new_with_context(context)
        settings = web.get_settings()
        settings.set_enable_developer_extras(False)
        settings.set_enable_page_cache(False)
        settings.set_enable_offline_web_application_cache(False)
        settings.set_enable_html5_database(False)

        def decide(_view, decision, decision_type):
            request = decision.get_request() if hasattr(decision, "get_request") else None
            uri = request.get_uri() if request is not None else None
            try:
                if uri is not None:
                    validated_url(uri)
            except ValueError:
                decision.ignore()
                return True
            if decision_type == WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION and uri is not None:
                web.load_uri(uri)
                decision.ignore()
                return True
            return False

        web.connect("decide-policy", decide)
        web.connect("permission-request", lambda _view, request: (request.deny(), True)[1])
        context.connect("download-started", lambda _context, download: download.cancel())
        layout.pack_start(web, True, True, 0)
        window.add(layout)
        window.show_all()
        web.load_uri(portal)
        Gtk.main()
    recheck()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError):
        raise SystemExit(3)
