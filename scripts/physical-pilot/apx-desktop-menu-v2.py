#!/usr/bin/env python3
"""ASCII context menus used by the common APX Waybar profile."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time

CLIENT = "/run/apx/host-services-client-v2.py"
CLIENT_V3 = "/run/apx/host-services-client-v3.py"


def run(arguments: tuple[str, ...], *, input_text: str | None = None):
    environment = dict(os.environ)
    environment.update({"PATH": "/usr/bin", "LC_ALL": "C"})
    return subprocess.run(arguments, input=input_text, text=True, capture_output=True, check=False,
                          env=environment)


def choose(title: str, choices: list[str]) -> str | None:
    result = run(("/usr/bin/rofi", "-dmenu", "-i", "-p", title, "-format", "s"),
                 input_text="\n".join(choices) + "\n")
    return result.stdout.rstrip("\n") if result.returncode == 0 else None


def secret(title: str) -> str | None:
    result = run(("/usr/bin/rofi", "-dmenu", "-password", "-p", title, "-format", "s"))
    return result.stdout.rstrip("\n") if result.returncode == 0 else None


def host(operation: str = "status", target: str | None = None) -> dict:
    arguments = (CLIENT, operation) + ((target,) if target is not None else ())
    result = run(arguments)
    if result.returncode:
        return {}
    return json.loads(result.stdout)


def host_v3(operation: str, target: str | None = None, credential: str | None = None) -> dict:
    arguments = (CLIENT_V3, operation) + ((target,) if target is not None else ())
    if credential is not None: arguments += ("--credential-stdin",)
    result = run(arguments, input_text=(credential + "\n") if credential is not None else None)
    if result.returncode: return {}
    return json.loads(result.stdout)


def bluetooth_pair_respond(session_id: str, accept: bool, pin: str | None = None) -> dict:
    arguments = (CLIENT_V3, "bluetooth-pair-respond", session_id, "--accept", "yes" if accept else "no")
    if pin is not None: arguments += ("--credential-stdin",)
    result = run(arguments, input_text=(pin + "\n") if pin is not None else None)
    if result.returncode: return {}
    return json.loads(result.stdout)


def wifi() -> None:
    state = host_v3("wifi-status")
    if not state:
        state = host(); current = state.get("network_name")
        networks = [{"known": name in set(state.get("known_networks", ())), "security": "unknown",
                     "signal": 0, "ssid": name} for name in state.get("available_networks", ())]
    else:
        current = state.get("network"); networks = state.get("networks", ())
    choices = [f"[ STATUS ] {current or 'disconnected'}", "[ SCAN ] procurar redes"]
    if current: choices.append("[ DISCONNECT ] desligar rede atual")
    actions = {}
    for network in networks:
        if network["ssid"] == current: continue
        security = network.get("security", "unknown"); signal = network.get("signal", 0)
        label = f"[ CONNECT ] {network['ssid']} :: {security} :: {signal}%"
        choices.append(label); actions[label] = network
    selected = choose("[ WIFI MENU ]", choices)
    if selected == "[ SCAN ] procurar redes": host_v3("wifi-scan") or host("wifi-scan")
    elif selected == "[ DISCONNECT ] desligar rede atual": host_v3("wifi-disconnect") or host("wifi-disconnect")
    elif selected in actions:
        network = actions[selected]; credential = None
        if not network.get("known") and network.get("security") not in {"open"}:
            credential = secret("[ WIFI PASSPHRASE ]")
            if credential is None: return
        host_v3("wifi-connect", network["ssid"], credential)


def bluetooth() -> None:
    state = host_v3("bluetooth-status")
    if not state:
        legacy = host(); powered = legacy.get("bluetooth_powered", False)
        state = {"powered": powered, "devices": legacy.get("bluetooth_devices", ())}
    powered = state.get("powered", False)
    choices = [f"[ POWER ] {'desligar' if powered else 'ligar'} Bluetooth"]
    if powered: choices.append("[ SCAN ] procurar dispositivos durante 8 segundos")
    actions = {}
    for device in state.get("devices", ()):
        if device.get("paired"):
            action = "DISCONNECT" if device.get("connected") else "CONNECT"
            label = f"[ {action} ] {device['name']} :: {device['address']}"; choices.append(label)
            actions[label] = ("bluetooth-disconnect" if device.get("connected") else "bluetooth-connect", device)
            forget = f"[ REMOVE ] {device['name']} :: {device['address']}"; choices.append(forget)
            actions[forget] = ("bluetooth-remove", device)
        else:
            label = f"[ PAIR ] {device['name']} :: {device['address']}"; choices.append(label)
            actions[label] = ("bluetooth-pair", device)
    selected = choose("[ BLUETOOTH MENU ]", choices)
    if selected == choices[0]: host_v3("bluetooth-power", "off" if powered else "on")
    elif selected == "[ SCAN ] procurar dispositivos durante 8 segundos": host_v3("bluetooth-scan")
    elif selected in actions:
        operation, device = actions[selected]
        if operation == "bluetooth-remove":
            confirmed = choose("[ CONFIRMAR REMOÇÃO ]", [f"[ CANCEL ] manter {device['name']}",
                                                         f"[ REMOVE ] esquecer {device['name']}"])
            if confirmed and confirmed.startswith("[ REMOVE ]"): host_v3(operation, device["address"])
        elif operation == "bluetooth-pair": bluetooth_pair(device)
        else: host_v3(operation, device["address"])


def bluetooth_pair(device: dict) -> None:
    session = host_v3("bluetooth-pair", device["address"])
    session_id = session.get("session_id")
    if type(session_id) is not str: return
    seen = None
    deadline = time.monotonic() + 125
    while time.monotonic() < deadline:
        phase, challenge = session.get("phase"), session.get("challenge")
        marker = (phase, challenge, session.get("passkey"))
        if phase == "completed":
            choose("[ BLUETOOTH ]", [f"[ OK ] {device['name']} emparelhado e confiável"]); return
        if phase == "failed":
            choose("[ BLUETOOTH ]", [f"[ FAILED ] {session.get('message', 'emparelhamento falhou')}"]); return
        if marker != seen and phase == "needs-response" and challenge == "confirm":
            code = session.get("passkey", "??????")
            answer = choose("[ CONFIRMAR CÓDIGO ]", [f"[ YES ] {code} coincide", "[ NO ] cancelar"])
            session = bluetooth_pair_respond(session_id, bool(answer and answer.startswith("[ YES ]")))
        elif marker != seen and phase == "needs-response" and challenge == "pin":
            pin = secret("[ BLUETOOTH PIN ]")
            session = bluetooth_pair_respond(session_id, pin is not None, pin)
        elif marker != seen and phase == "waiting-device":
            choose("[ ESCREVA NO DISPOSITIVO ]", [f"[ CONTINUE ] código {session.get('passkey', '??????')}"])
        else:
            time.sleep(0.5)
            session = host_v3("bluetooth-pair-status", session_id)
        seen = marker


def audio() -> None:
    choices = ["[ MUTE ] alternar som", "[ VOL +5 ] aumentar", "[ VOL -5 ] diminuir", "[ ADVANCED ] abrir pavucontrol"]
    outputs = {}
    status = run(("/usr/bin/wpctl", "status", "-n"))
    in_sinks = False
    for line in status.stdout.splitlines():
        if "Sinks:" in line:
            in_sinks = True; continue
        if in_sinks and "Sources:" in line:
            break
        if in_sinks:
            match = re.search(r"\*?\s*([0-9]+)\.\s+(.+?)(?:\s+\[vol:|$)", line)
            if match:
                label = f"[ OUTPUT ] {match.group(2).strip()} :: {match.group(1)}"
                choices.append(label); outputs[label] = match.group(1)
    if not Path("/usr/bin/pavucontrol").is_file():
        choices.remove("[ ADVANCED ] abrir pavucontrol")
    selected = choose("[ AUDIO MENU ]", choices)
    actions = {
        choices[0]: ("/usr/bin/wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"),
        choices[1]: ("/usr/bin/wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SINK@", "5%+"),
        choices[2]: ("/usr/bin/wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"),
        choices[3]: ("/usr/bin/pavucontrol",),
    }
    if selected in actions: subprocess.Popen(actions[selected], start_new_session=True)
    elif selected in outputs: run(("/usr/bin/wpctl", "set-default", outputs[selected]))


def battery() -> None:
    supplies = []
    for directory in sorted(Path("/sys/class/power_supply").glob("BAT*")):
        def read(name: str) -> str:
            try: return (directory / name).read_text().strip()
            except OSError: return "?"
        supplies.extend((f"[ BATTERY ] {directory.name}", f"[ CHARGE ] {read('capacity')}%",
                         f"[ STATE ] {read('status')}", "[ POWER PROFILE ] Host backend unavailable"))
    choose("[ BATTERY MENU ]", supplies or ["[ BATTERY ] unavailable"])


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("menu", choices=("wifi", "bluetooth", "audio", "battery"))
    globals()[parser.parse_args().menu](); return 0


if __name__ == "__main__": raise SystemExit(main())
