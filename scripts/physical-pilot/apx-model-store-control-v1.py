#!/usr/bin/env python3
"""Authenticated official-Hub control surface for the external model store."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import threading
import select
import time

sys.path.insert(0, "/usr/lib/apx")
from apx_host_services_peer import HostServicesPeer, authorize_official_hub_peer  # noqa: E402


SOCKET = Path("/run/apx/model-store-control-v1.sock")
LIVE_SOCKET = Path("/var/lib/apx/environments/hub/home/.apx-host-bridge/model-store-control-v1.sock")
ADAPTER = "/usr/lib/apx/apx-model-store-v1.py"
HOST_MOUNT_NS = ("/usr/bin/nsenter", "--target", "1", "--mount", "--")
STORE_UNIT = "apx-model-store-v1.service"
OLLAMA_UNIT = "apx-ollama-v1.service"
MAX_MESSAGE_BYTES = 4096
LOCK = threading.Lock()
TRANSITION_LOCK = threading.Lock()
TRANSITION: dict[str, object] | None = None
SELECTION_DIRECTORY = Path("/var/lib/apx/model-selection-v1")
SELECTION_FILE = SELECTION_DIRECTORY / "selected"
MODELS = {
    "fast": {
        "id": "qwen2.5-coder:3b",
        "label": "Qwen2.5-Coder 3B Fast",
        "detail": "CUDA · resposta rápida",
        "load_seconds": 10,
    },
    "balanced": {
        "id": "qwen2.5-coder:7b",
        "label": "Qwen2.5-Coder 7B",
        "detail": "CUDA · maior capacidade",
        "load_seconds": 20,
    },
    "quality": {
        "id": "qwen3-coder:30b",
        "label": "Qwen3-Coder 30B",
        "detail": "CUDA + CPU · máxima qualidade",
        "load_seconds": 75,
    },
}


def run(*arguments: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, text=True, capture_output=True, check=False, timeout=timeout,
        env={"PATH": "/usr/bin", "LC_ALL": "C"},
    )


def unit_active(unit: str) -> bool:
    return run("/usr/bin/systemctl", "is-active", "--quiet", unit, timeout=10).returncode == 0


def reset_failed(*units: str) -> None:
    # An inactive unit may already be garbage-collected, in which case
    # reset-failed reports "not loaded". The following start/stop operation is
    # authoritative and still reports genuine service failures.
    run("/usr/bin/systemctl", "reset-failed", *units, timeout=15)


def selected_profile() -> str:
    try:
        value = SELECTION_FILE.read_text(encoding="ascii").strip()
    except FileNotFoundError:
        return "fast"
    if value not in MODELS:
        raise RuntimeError("a seleção persistente do modelo é inválida")
    return value


def save_selected_profile(profile: str) -> None:
    if profile not in MODELS:
        raise ValueError("o perfil de modelo pedido não existe")
    SELECTION_DIRECTORY.mkdir(mode=0o755, parents=True, exist_ok=True)
    temporary = SELECTION_DIRECTORY / "selected.new"
    temporary.write_text(profile + "\n", encoding="ascii")
    os.chown(temporary, 0, 0)
    os.chmod(temporary, 0o644)
    os.replace(temporary, SELECTION_FILE)


def set_transition(profile: str, phase: str) -> None:
    global TRANSITION
    with TRANSITION_LOCK:
        TRANSITION = {
            "profile": profile,
            "phase": phase,
            "started": time.monotonic(),
        }


def clear_transition() -> None:
    global TRANSITION
    with TRANSITION_LOCK:
        TRANSITION = None


def transition_state() -> dict[str, object] | None:
    with TRANSITION_LOCK:
        current = None if TRANSITION is None else dict(TRANSITION)
    if current is None:
        return None
    profile = str(current["profile"])
    phase = str(current["phase"])
    if phase == "stopping":
        progress = 8
        message = "A parar o modelo anterior…"
    elif phase == "rollback":
        progress = 50
        message = "A repor o modelo anterior…"
    else:
        elapsed = max(0.0, time.monotonic() - float(current["started"]))
        expected = int(MODELS[profile]["load_seconds"])
        progress = min(95, 18 + int(77 * elapsed / expected))
        message = "A carregar os pesos e a preparar o contexto…"
    return {
        "model_transition": True,
        "transition_profile": profile,
        "transition_model": MODELS[profile]["label"],
        "transition_progress": progress,
        "transition_message": message,
    }


def state() -> dict[str, object]:
    # ProtectSystem/ReadWritePaths give this controller a private mount view.
    # Inspect only through PID 1's Host mount namespace so the Hub sees the
    # authoritative read-only Btrfs mount rather than the sandbox bind mount.
    observed = run(*HOST_MOUNT_NS, ADAPTER, "status", timeout=15)
    if observed.returncode:
        raise RuntimeError("could not inspect the admitted model store")
    value = json.loads(observed.stdout)
    profile = selected_profile()
    value.update({
        "server_active": unit_active(OLLAMA_UNIT),
        "store_active": unit_active(STORE_UNIT),
        "selected_profile": profile,
        "selected_model": MODELS[profile]["id"],
        "model": MODELS[profile]["label"],
        "model_detail": MODELS[profile]["detail"],
        "models": [
            {name: value for name, value in dict(profile=key, **definition).items()
             if name != "load_seconds"}
            for key, definition in MODELS.items()
        ],
    })
    transition = transition_state()
    if transition is not None:
        value.update(transition)
        value["state"] = "model-loading"
        value["message"] = transition["transition_message"]
        return value
    value["model_transition"] = False
    if value["mounted"] and value["read_only"] and value["server_active"]:
        value["state"] = "active"
        value["message"] = "Modelo local ativo; SSD protegido em modo só de leitura."
    elif value["mounted"] and value["read_only"] and not value["server_active"]:
        value["state"] = "model-stopped"
        value["message"] = "Modelo desativado; SSD continua montado em modo só de leitura."
    elif value["device_present"] and not value["mapped"] and not value["mounted"]:
        value["state"] = "safe-to-remove"
        value["message"] = "Modelo parado. Já pode remover o SSD com segurança."
    elif not value["device_present"]:
        value["state"] = "absent"
        value["message"] = "SSD do modelo não está ligado."
    else:
        value["state"] = "transition"
        value["message"] = "O armazenamento do modelo está a mudar de estado."
    return value


def apply(operation: str, payload: dict[str, object]) -> dict[str, object]:
    if operation == "status":
        if payload:
            raise ValueError("status payload differs")
        return state()
    if operation == "storage-activate":
        if payload != {"confirmation": "MONTAR SSD"}:
            raise ValueError("explicit storage activation confirmation differs")
        reset_failed(STORE_UNIT, OLLAMA_UNIT)
        result = run("/usr/bin/systemctl", "start", STORE_UNIT)
        if result.returncode:
            raise RuntimeError("não foi possível montar o SSD")
        current = state()
        if not current["mounted"] or not current["read_only"]:
            raise RuntimeError("o SSD não atingiu o estado montado protegido")
        return current
    if operation == "model-start":
        if payload != {"confirmation": "ATIVAR MODELO"}:
            raise ValueError("explicit model activation confirmation differs")
        current = state()
        if not current["mounted"] or not current["read_only"]:
            raise RuntimeError("monte primeiro o SSD do modelo")
        reset_failed(OLLAMA_UNIT)
        result = run("/usr/bin/systemctl", "start", OLLAMA_UNIT, timeout=300)
        if result.returncode:
            raise RuntimeError("não foi possível ativar o modelo")
        current = state()
        if not current["server_active"]:
            raise RuntimeError("o modelo não atingiu o estado ativo")
        return current
    if operation == "model-select":
        if set(payload) != {"confirmation", "profile"} \
                or payload["confirmation"] != "SELECIONAR MODELO" \
                or type(payload["profile"]) is not str \
                or payload["profile"] not in MODELS:
            raise ValueError("explicit model selection confirmation differs")
        current = state()
        if not current["mounted"] or not current["read_only"]:
            raise RuntimeError("monte primeiro o SSD do modelo")
        previous = selected_profile()
        requested = payload["profile"]
        if requested == previous:
            return current
        was_active = bool(current["server_active"])
        set_transition(requested, "stopping")
        try:
            if was_active:
                result = run("/usr/bin/systemctl", "stop", OLLAMA_UNIT)
                if result.returncode:
                    raise RuntimeError("não foi possível parar o modelo atual")
            save_selected_profile(requested)
            if was_active:
                set_transition(requested, "loading")
                reset_failed(OLLAMA_UNIT)
                result = run("/usr/bin/systemctl", "start", OLLAMA_UNIT, timeout=300)
                if result.returncode:
                    set_transition(previous, "rollback")
                    save_selected_profile(previous)
                    run("/usr/bin/systemctl", "start", OLLAMA_UNIT, timeout=300)
                    raise RuntimeError("não foi possível carregar o modelo selecionado; seleção anterior reposta")
            clear_transition()
            return state()
        finally:
            clear_transition()
    if operation == "model-stop":
        if payload != {"confirmation": "DESATIVAR MODELO"}:
            raise ValueError("explicit model deactivation confirmation differs")
        result = run("/usr/bin/systemctl", "stop", OLLAMA_UNIT)
        if result.returncode:
            raise RuntimeError("não foi possível desativar o modelo")
        current = state()
        if current["server_active"] or not current["mounted"]:
            raise RuntimeError("o modelo não parou mantendo o SSD montado")
        return current
    if operation == "safe-detach":
        if payload != {"confirmation": "REMOVER COM SEGURANÇA"}:
            raise ValueError("explicit safe-detach confirmation differs")
        result = run("/usr/bin/systemctl", "stop", STORE_UNIT)
        if result.returncode:
            raise RuntimeError("não foi possível parar e desmontar o SSD")
        current = state()
        if current["mapped"] or current["mounted"] or current["server_active"]:
            raise RuntimeError("o SSD continua ocupado; não deve ser removido")
        reset_failed(STORE_UNIT, OLLAMA_UNIT)
        return current
    raise ValueError("unsupported model-store operation")


def receive(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
        chunk = connection.recv(min(1024, MAX_MESSAGE_BYTES + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    if not data.endswith(b"\n") or len(data) > MAX_MESSAGE_BYTES or b"\n" in data[:-1]:
        raise ValueError("request framing differs")
    return bytes(data)


def respond(connection: socket.socket) -> None:
    try:
        pid, uid, gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        authorize_official_hub_peer(HostServicesPeer(pid, uid, gid))
        request = json.loads(receive(connection))
        if type(request) is not dict or set(request) != {"operation", "payload"} \
                or type(request["operation"]) is not str or type(request["payload"]) is not dict:
            raise ValueError("request differs")
        if request["operation"] == "status":
            result = apply(request["operation"], request["payload"])
        else:
            with LOCK:
                result = apply(request["operation"], request["payload"])
        response = {"ok": True, "result": result, "error": None}
    except Exception as error:
        response = {"ok": False, "result": None, "error": str(error)[:300]}
    connection.sendall((json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode())


def handle_connection(connection: socket.socket) -> None:
    with connection:
        respond(connection)


def serve() -> None:
    if os.geteuid() != 0:
        raise RuntimeError("the model-store controller requires Host root")
    SOCKET.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    live_parent = LIVE_SOCKET.parent
    metadata = live_parent.stat()
    if metadata.st_uid != 0 or metadata.st_gid != 0 or metadata.st_mode & 0o022:
        raise RuntimeError("live Hub bridge directory identity differs")
    servers: list[socket.socket] = []
    try:
        for endpoint in (SOCKET, LIVE_SOCKET):
            endpoint.unlink(missing_ok=True)
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(str(endpoint))
            # The live bridge has a root-owned, non-writable parent. Peer UID,
            # namespace, registration and official-Hub cgroup remain mandatory.
            os.chmod(endpoint, 0o600 if endpoint == SOCKET else 0o666)
            server.listen(8)
            servers.append(server)
        while True:
            readable, _, _ = select.select(servers, [], [])
            for server in readable:
                connection, _ = server.accept()
                threading.Thread(
                    target=handle_connection, args=(connection,), daemon=True,
                    name="apx-model-store-client",
                ).start()
    finally:
        for server in servers:
            server.close()


if __name__ == "__main__":
    if sys.argv != [sys.argv[0], "--serve"]:
        raise SystemExit("usage: apx-model-store-control-v1.py --serve")
    serve()
