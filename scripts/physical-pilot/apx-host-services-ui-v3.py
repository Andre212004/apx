#!/usr/bin/env python3
"""Compatibility adapter from the current Quickshell model to Host services v3."""

from __future__ import annotations

import json
import os
import subprocess
import sys

V2 = "/run/apx/host-services-client-v2.py"
V3 = "/run/apx/host-services-client-v3.py"
CAPTIVE_BROWSER = "/usr/local/lib/apx/apx-captive-portal-browser-v1.py"


def run(arguments: tuple[str, ...], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, input=input_text, text=True, capture_output=True, check=False,
                          env={**os.environ, "PATH": "/usr/bin", "LC_ALL": "C"})


def data(arguments: tuple[str, ...], input_text: str | None = None) -> dict:
    result = run(arguments, input_text)
    if result.returncode: raise RuntimeError((result.stderr or "Host service unavailable").strip())
    value = json.loads(result.stdout)
    if type(value) is not dict: raise RuntimeError("Host service returned invalid state")
    return value


def status() -> dict:
    legacy = data((V2, "status")); network = data((V3, "wifi-status")); bluetooth = data((V3, "bluetooth-status"))
    details = network.get("networks", [])
    legacy.update({
        "available_networks": [item["ssid"] for item in details],
        "known_networks": [item["ssid"] for item in details if item.get("known")],
        "network_details": details,
        "network_connectivity": network.get("connectivity", "unknown"),
        "network_connectivity_checked_at": network.get("connectivity_checked_at"),
        "network_name": network.get("network"),
        "network_portal": network.get("portal", {"required": False, "url": None, "source": None}),
        "open_networks": [item["ssid"] for item in details if item.get("security") == "open"],
        "bluetooth_devices": bluetooth.get("devices", []),
        "bluetooth_discovering": bluetooth.get("discovering", False),
        "bluetooth_pairable": bluetooth.get("pairable", False),
        "bluetooth_powered": bluetooth.get("powered", False),
    })
    return legacy


def wifi_connect(ssid: str) -> dict:
    network = data((V3, "wifi-status"))
    target = next((item for item in network.get("networks", []) if item.get("ssid") == ssid), None)
    if target is None: raise RuntimeError("A rede já não está disponível; atualize a pesquisa")
    arguments = (V3, "wifi-connect", ssid)
    if target.get("known") or target.get("security") == "open": return data(arguments)
    if target.get("security") == "enterprise": raise RuntimeError("Wi-Fi enterprise ainda não é suportado")
    prompt = run(("/usr/bin/rofi", "-dmenu", "-password", "-p", "[ WIFI PASSPHRASE ]", "-format", "s"))
    if prompt.returncode: raise RuntimeError("Ligação Wi-Fi cancelada")
    secret = prompt.stdout.rstrip("\n")
    try: return data(arguments + ("--credential-stdin",), secret + "\n")
    finally: secret = ""


def portal_open() -> dict:
    portal = data((V3, "wifi-portal-open"))
    url = portal.get("url")
    if type(url) is not str or portal.get("handler") != "environment-browser":
        raise RuntimeError("O HOST não devolveu um portal válido")
    process = subprocess.Popen((CAPTIVE_BROWSER,), stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, text=True, start_new_session=True,
                               env={**os.environ, "PATH": "/usr/bin"})
    if process.stdin is None:
        raise RuntimeError("Não foi possível abrir a autenticação Wi-Fi")
    process.stdin.write(url + "\n")
    process.stdin.close()
    process.stdin = None
    return {"opened": True, "handler": "isolated-environment-window"}


def main() -> int:
    if len(sys.argv) not in {2, 3}: raise RuntimeError("Uso: cliente OPERAÇÃO [ALVO]")
    operation = sys.argv[1]; target = sys.argv[2] if len(sys.argv) == 3 else None
    if operation == "status" and target is None: result = status()
    elif operation == "wifi-connect" and target is not None: result = wifi_connect(target)
    elif operation == "wifi-portal-open" and target is None: result = portal_open()
    elif operation in {"wifi-scan", "wifi-disconnect", "wifi-connectivity-check"} and target is None:
        result = data((V3, operation))
    elif operation in {"bluetooth-power", "bluetooth-connect", "bluetooth-disconnect"} and target is not None:
        mapped = {"bluetooth-power": "bluetooth-power", "bluetooth-connect": "bluetooth-connect",
                  "bluetooth-disconnect": "bluetooth-disconnect"}[operation]
        result = data((V3, mapped, target))
    else: raise RuntimeError("Operação da interface não suportada")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"APX Host UI services unavailable: {error}", file=sys.stderr); raise SystemExit(3)
