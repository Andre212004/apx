#!/usr/bin/env python3
"""Unprivileged fixed-action client for the APX Environment switch trial."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
from pathlib import Path

# The Host-installed contract is authoritative. Do not let stale helper
# modules beside the bridged client override the current module catalogue.
sys.path.insert(0, "/usr/lib/apx")
from apx_environment_switch_contract import MAX_MESSAGE_BYTES, request_bytes  # noqa: E402


PRIMARY_SOCKET = Path("/run/apx/environment-switch-v1.sock")
LIVE_SOCKET = Path("/home/.apx-host-bridge/environment-switch-v1.sock")


def connect() -> socket.socket:
    last_error: OSError | None = None
    for endpoint in (PRIMARY_SOCKET, LIVE_SOCKET):
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(10)
        try:
            connection.connect(str(endpoint))
            return connection
        except OSError as error:
            last_error = error
            connection.close()
    if last_error is not None:
        raise last_error
    raise FileNotFoundError("nenhum endpoint de Environments está disponível")


def exchange(operation: str, target: str | None = None, generation: str | None = None,
             description: str | None = None, preset: str | None = None,
             modules: list[str] | None = None):
    with connect() as connection:
        connection.sendall(request_bytes(operation, target, generation, description, preset, modules))
        data = bytearray()
        while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
            chunk = connection.recv(4096)
            if not chunk:
                break
            data.extend(chunk)
    value = json.loads(data)
    if type(value) is not dict or value.get("ok") is not True:
        error = value.get("error", {}) if type(value) is dict else {}
        raise RuntimeError(str(error.get("message", "pedido recusado")))
    return value["result"]


def hub_menu() -> int:
    """Compatibility action for older bars: open the native QuickShell panel."""
    result = subprocess.run((
        "/usr/bin/qs", "--path", "/home/apx/.config/quickshell/apx/shell.qml",
        "ipc", "call", "host", "openEnvironments",
    ), text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("não foi possível abrir o painel de Environments")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("catalog", "create", "destroy", "hub-menu", "identity", "management-status",
                                         "open", "return", "status", "waybar-identity"))
    parser.add_argument("--target")
    parser.add_argument("--generation")
    parser.add_argument("--description")
    parser.add_argument("--preset", choices=("basic", "intermediate", "complete"))
    parser.add_argument("--modules")
    arguments = parser.parse_args(); mode = arguments.mode
    if mode == "hub-menu":
        return hub_menu()
    operation = {"catalog": "catalog.get", "create": "environment.create",
                 "destroy": "environment.destroy", "identity": "identity.get",
                 "management-status": "management.status", "open": "switch.to-workload",
                 "return": "return.to-hub", "status": "status.get",
                 "waybar-identity": "identity.get"}[mode]
    if mode in {"create", "open"} and arguments.target is None:
        parser.error(mode + " requires --target")
    if mode == "destroy" and (arguments.target is None or arguments.generation is None):
        parser.error("destroy requires --target and --generation")
    if mode != "create" and (arguments.description is not None or arguments.preset is not None or arguments.modules is not None):
        parser.error("creation options are only valid when creating an Environment")
    if mode not in {"create", "destroy", "open"} and (arguments.target is not None or arguments.generation is not None):
        parser.error(mode + " takes no target")
    modules = arguments.modules.split(",") if arguments.modules else None
    value = exchange(operation, arguments.target, arguments.generation, arguments.description,
                     arguments.preset, modules)
    if mode == "waybar-identity":
        label = value.get("display_name", value.get("name", "?"))
        role = str(value.get("role", "unknown"))
        is_hub = role == "hub"
        text = "[ APX · HUB · ENVIRONMENTS ]" if is_hub \
            else f"[ APX · {str(label).upper()} · VOLTAR AO HUB ]"
        action = "Gerir e abrir Environments" if is_hub else "Fechar este Environment e regressar ao HUB"
        tooltip = "\n".join((
            action,
            f"Nome: {label} ({value.get('name', '?')})",
            f"Categoria: {value.get('category', 'general')}",
            f"Release: {value.get('release', '?')}",
            "Restauro de sessão: " + ("ligado" if value.get("session_restore") is True else "desligado"),
            "Atualizações: " + ("coordenadas com o Host" if value.get("update_policy") == "follow-host"
                                else "política independente"),
        ))
        print(json.dumps({"class": role, "text": text, "tooltip": tooltip},
                         ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"APX recusou a troca: {error}", file=sys.stderr)
        raise SystemExit(2)
