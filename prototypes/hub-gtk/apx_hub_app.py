#!/usr/bin/env python3
"""Non-privileged GTK APX session client using closed Host-issued actions."""

from __future__ import annotations

import argparse

from apx_desktop_session import (  # noqa: E402
    DesktopSessionError, execute_desktop_action, load_desktop_session,
)
from apx_session_control import build_session_control  # noqa: E402


def run_gui(switcher: bool, management: bool) -> int:
    """Load GTK only after the non-graphical CLI trust checks have passed."""
    try:
        import gi
    except ModuleNotFoundError as error:
        raise SystemExit("APX Hub prototype requires python-gobject inside its graphical Environment") from error

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gtk

    try:
        session = load_desktop_session()
    except DesktopSessionError as error:
        raise SystemExit(f"APX recusou abrir os controlos: {error}") from error
    control = build_session_control(session.role)
    if management and not control.management_enabled:
        raise SystemExit("A gestão de Environments só está disponível no HUB")

    class HubWindow(Adw.ApplicationWindow):
        def __init__(self, application: Adw.Application):
            super().__init__(application=application, title=control.title)
            self.set_default_size(420 if switcher else 960, 540 if switcher else 700)
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            content.set_margin_top(18); content.set_margin_bottom(18)
            content.set_margin_start(18); content.set_margin_end(18)
            content.append(Gtk.Label(label=control.title, xalign=0))
            status = Gtk.Label(label="Pronto", xalign=0)
            content.append(status)

            def invoke(_button, action):
                _button.set_sensitive(False)
                status.set_label("A trocar de Environment…")
                try:
                    response = execute_desktop_action(action)
                except Exception as error:
                    status.set_label(f"Operação recusada: {error}")
                    _button.set_sensitive(True)
                    return
                if response.classification != "accepted":
                    status.set_label("Operação não concluída: " + "; ".join(response.issues))
                    _button.set_sensitive(True)

            for action in session.actions:
                button = Gtk.Button(label=action.label)
                button.set_tooltip_text("Pedido APX fechado e validado pelo Host")
                button.connect("clicked", invoke, action)
                content.append(button)
            self.set_content(content)

    class HubApplication(Adw.Application):
        def __init__(self):
            super().__init__(application_id="org.apx.SessionControl")

        def do_activate(self):
            HubWindow(self).present()

    return HubApplication().run([])


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--switcher", action="store_true")
    mode.add_argument("--management", action="store_true")
    args = parser.parse_args()
    return run_gui(args.switcher, args.management)


if __name__ == "__main__":
    raise SystemExit(main())
