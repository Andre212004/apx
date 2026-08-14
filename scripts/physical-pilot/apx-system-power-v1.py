#!/usr/bin/env python3
"""Authenticated two-step reboot/poweroff authority for the exact APX Hub."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import select
import socket
import struct
import subprocess
import sys
import threading
import time

sys.path.insert(0, "/usr/lib/apx")
from apx_host_services_peer import HostServicesPeer, authorize_official_hub_peer  # noqa: E402
from apx_system_power_contract import MAX_MESSAGE_BYTES, PROFILE, parse_message  # noqa: E402

SOCKET = Path("/run/apx/system-power-v1.sock")
LIVE_SOCKET = Path("/var/lib/apx/environments/hub/home/.apx-host-bridge/system-power-v1.sock")
RESERVATION = Path("/run/apx/system-power-v1.reserved")
TRANSITION_LOCK = Path("/run/apx/machine-transition-v1.lock")
STATE_DIR = Path("/var/lib/apx/system-power-v1")
STATUS = STATE_DIR / "status.json"
AUDIT = STATE_DIR / "audit.jsonl"
HARDWARE_STATUS = STATE_DIR / "hardware-profile.json"
ACTIVE = Path("/run/apx/official-hub-graphical-v1.json")
RUNNER = "/usr/lib/apx/apx-system-power-runner-v1.py"
OFFICIAL_UNIT = "/system.slice/apx-official-hub-graphical-6f63f9a9.service"
TTL_SECONDS = 30
LOCK = threading.Lock()
PENDING: dict[str, object] | None = None
LAST_PREPARE = 0.0
GPU_BRIDGE = Path("/sys/kernel/apx_legion_gpu_profile_v1")
DISPLAY_BACKLIGHT_CLASS = Path("/sys/class/backlight")
KEYBOARD_BACKLIGHT = Path("/sys/class/leds/platform::kbd_backlight")
PLATFORM_PROFILE = Path("/sys/firmware/acpi/platform_profile")
PLATFORM_CHOICES = Path("/sys/firmware/acpi/platform_profile_choices")
BOOT_ID = Path("/proc/sys/kernel/random/boot_id")


def atomic(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()); os.fsync(descriptor)
    finally: os.close(descriptor)
    os.replace(temporary, path)


def audit(event: str, action: str | None, result: str, peer_uid: int | None = None) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    record = {"schema": 1, "profile": PROFILE, "time": int(time.time()), "event": event,
              "action": action, "result": result, "environment": "hub", "peer_uid": peer_uid}
    descriptor = os.open(AUDIT, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try: os.write(descriptor, (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode())
    finally: os.close(descriptor)


def quickshell_parent(peer_pid: int, proc: Path = Path("/proc")) -> int:
    try:
        status = dict(line.split(":", 1) for line in (proc / str(peer_pid) / "status").read_text().splitlines() if ":" in line)
        parent = int(status["PPid"].strip())
        comm = (proc / str(parent) / "comm").read_text().strip()
        executable = os.readlink(proc / str(parent) / "exe")
        cgroups = (proc / str(parent) / "cgroup").read_text().splitlines()
    except (OSError, KeyError, ValueError) as error:
        raise PermissionError("Quickshell parent proof is unavailable") from error
    if parent <= 1 or comm != "quickshell" or executable != "/usr/bin/quickshell" \
            or not any(OFFICIAL_UNIT in line and line.split(":", 2)[-1].startswith(OFFICIAL_UNIT) for line in cgroups):
        raise PermissionError("power mutation caller is not a direct Quickshell child")
    return parent


def update_state() -> dict[str, object]:
    operations = Path("/var/lib/apx/coordinated-updates-v1/operations")
    candidates = sorted(operations.glob("*/status.json"), reverse=True)
    if not candidates: return {"state": "idle", "reboot_required": False}
    try:
        value = json.loads(candidates[0].read_text())
        return value if type(value) is dict else {"state": "unknown", "reboot_required": False}
    except (OSError, json.JSONDecodeError): return {"state": "unknown", "reboot_required": False}


def transition_busy() -> bool:
    TRANSITION_LOCK.touch(mode=0o600, exist_ok=True)
    descriptor = os.open(TRANSITION_LOCK, os.O_RDWR | os.O_NOFOLLOW)
    try:
        try: fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return True
        fcntl.flock(descriptor, fcntl.LOCK_UN); return False
    finally: os.close(descriptor)


def inhibitors(action: str) -> list[str]:
    result = subprocess.run(("/usr/bin/systemd-inhibit", "--list", "--mode=block", "--no-legend"),
                            text=True, capture_output=True, check=False, timeout=5,
                            env={"PATH": "/usr/bin", "LC_ALL": "C"})
    if result.returncode: return ["host-inhibitor-state-unavailable"]
    kind = "sleep" if action == "suspend" else "shutdown"
    return [" ".join(line.split())[:240] for line in result.stdout.splitlines()
            if line.strip() and kind in line.lower()]


def blockers(action: str) -> list[str]:
    result = []
    state = update_state().get("state")
    if state in {"preparing", "staged", "applying"}: result.append(f"coordinated-update-{state}")
    if transition_busy(): result.append("machine-transition-busy")
    result.extend(f"inhibitor:{item}" for item in inhibitors(action))
    return result


def reserve() -> None:
    descriptor = os.open(RESERVATION, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.write(descriptor, b"reserved\n"); os.close(descriptor)


def clear_pending(reason: str) -> None:
    global PENDING
    action = str(PENDING.get("action")) if PENDING else None
    PENDING = None; RESERVATION.unlink(missing_ok=True)
    atomic(STATUS, {"schema": 1, "profile": PROFILE, "state": reason, "action": action})


def _read_bounded(path: Path, allowed: set[str]) -> str:
    value = path.read_text(encoding="ascii").strip()
    if value not in allowed:
        raise RuntimeError(f"unexpected hardware value at {path}")
    return value


def _read_hardware_integer(path: Path, minimum: int, maximum: int) -> int:
    value = path.read_text(encoding="ascii").strip()
    if not value.isdecimal():
        raise RuntimeError(f"unexpected hardware value at {path}")
    number = int(value)
    if not minimum <= number <= maximum:
        raise RuntimeError(f"out-of-range hardware value at {path}")
    return number


def display_backlight() -> Path:
    """Resolve the internal AMD panel by hardware path, not boot-time card numbering."""
    candidates = []
    for candidate in DISPLAY_BACKLIGHT_CLASS.iterdir():
        if not re.fullmatch(r"amdgpu_bl[0-9]+", candidate.name):
            continue
        resolved = str(candidate.resolve(strict=True))
        if "/0000:05:00.0/drm/" in resolved:
            candidates.append(candidate)
    if len(candidates) != 1:
        raise RuntimeError("internal AMD display backlight is absent or ambiguous")
    return candidates[0]


def hardware_control_status() -> dict[str, object]:
    backlight = display_backlight()
    display_max = _read_hardware_integer(backlight / "max_brightness", 1, 65535)
    if display_max != 65535 or _read_bounded(backlight / "type", {"raw"}) != "raw":
        raise RuntimeError("internal AMD display backlight identity differs")
    display = _read_hardware_integer(backlight / "brightness", 0, display_max)
    keyboard_max = _read_hardware_integer(KEYBOARD_BACKLIGHT / "max_brightness", 1, 8)
    if keyboard_max != 2:
        raise RuntimeError("Lenovo keyboard backlight identity differs")
    keyboard = _read_hardware_integer(KEYBOARD_BACKLIGHT / "brightness", 0, keyboard_max)
    return {
        "display_brightness": round(display * 100 / display_max),
        "display_brightness_raw": display,
        "display_brightness_max": display_max,
        "keyboard_brightness": keyboard,
        "keyboard_brightness_max": keyboard_max,
    }


def _hardware_record() -> dict[str, object]:
    try:
        value = json.loads(HARDWARE_STATUS.read_text())
        return value if type(value) is dict and value.get("schema") == 1 else {}
    except (OSError, json.JSONDecodeError):
        return {}


def hardware_profile_status() -> dict[str, object]:
    choices = PLATFORM_CHOICES.read_text(encoding="ascii").split()
    required = {"low-power", "balanced", "performance"}
    if not required.issubset(choices):
        raise RuntimeError("required Lenovo platform profiles are unavailable")
    platform = _read_bounded(PLATFORM_PROFILE, set(choices))
    hybrid_supported = int(_read_bounded(GPU_BRIDGE / "hybrid_supported", {"0", "1", "2"}))
    igpu_supported = int(_read_bounded(GPU_BRIDGE / "igpu_supported", {"0", "1", "2"}))
    hybrid = _read_bounded(GPU_BRIDGE / "hybrid_mode", {"0", "1"}) == "1"
    boot_id = BOOT_ID.read_text(encoding="ascii").strip()
    record = _hardware_record()
    requested = record.get("requested_gpu")
    # Migrate the short-lived APX-only "amd" policy from the first pilot. This
    # Legion firmware exposes only Hybrid Graphics and discrete NVIDIA modes.
    if requested == "amd":
        requested = "hybrid"
    if requested not in {"hybrid", "nvidia"}:
        requested = "hybrid"
    reboot_required = bool(record.get("reboot_required")) and record.get("set_boot_id") == boot_id
    if record and not reboot_required and record.get("reboot_required"):
        record["reboot_required"] = False
        atomic(HARDWARE_STATUS, record)
    if reboot_required:
        active = record.get("previous_gpu", "hybrid")
        mismatch = False
    else:
        active = "hybrid" if hybrid else "nvidia"
        mismatch = active != requested
    return {
        "schema": 1, "platform_profile": platform,
        "platform_profiles": ["low-power", "balanced", "performance"],
        "gpu_profile": active, "requested_gpu_profile": requested,
        "gpu_profiles": ["hybrid", "nvidia"],
        "gpu_backend": "lenovo-wmi", "hybrid_supported": hybrid_supported,
        "igpu_firmware_supported": bool(igpu_supported),
        "reboot_required": reboot_required, "profile_mismatch": mismatch,
        **hardware_control_status(),
    }


def set_display_brightness(percent: int) -> dict[str, object]:
    if type(percent) is not int or not 5 <= percent <= 100:
        raise ValueError("display brightness must be an integer from 5 to 100")
    status = hardware_control_status()
    maximum = int(status["display_brightness_max"])
    target = max(1, round(maximum * percent / 100))
    (display_backlight() / "brightness").write_text(f"{target}\n", encoding="ascii")
    observed = hardware_control_status()
    if abs(int(observed["display_brightness"]) - percent) > 1:
        raise RuntimeError("AMD display backlight did not apply the requested brightness")
    return observed


def cycle_keyboard_brightness() -> dict[str, object]:
    status = hardware_control_status()
    maximum = int(status["keyboard_brightness_max"])
    target = (int(status["keyboard_brightness"]) + 1) % (maximum + 1)
    (KEYBOARD_BACKLIGHT / "brightness").write_text(f"{target}\n", encoding="ascii")
    observed = hardware_control_status()
    if observed["keyboard_brightness"] != target:
        raise RuntimeError("Lenovo keyboard backlight did not apply the next level")
    return observed


def set_platform_profile(profile: str) -> dict[str, object]:
    if profile not in {"low-power", "balanced", "performance"}:
        raise ValueError("unsupported platform profile")
    status = hardware_profile_status()
    if profile not in status["platform_profiles"]:
        raise RuntimeError("requested platform profile is unavailable")
    PLATFORM_PROFILE.write_text(profile + "\n", encoding="ascii")
    observed = _read_bounded(PLATFORM_PROFILE, set(status["platform_profiles"]))
    if observed != profile:
        raise RuntimeError("Lenovo firmware did not apply the platform profile")
    return hardware_profile_status()


def set_gpu_profile(profile: str) -> dict[str, object]:
    if profile not in {"hybrid", "nvidia"}:
        raise ValueError("unsupported GPU profile")
    before = hardware_profile_status()
    if not before["hybrid_supported"]:
        raise RuntimeError("Lenovo Hybrid Graphics control is unavailable")
    wanted_hybrid = profile != "nvidia"
    (GPU_BRIDGE / "hybrid_mode").write_text("1\n" if wanted_hybrid else "0\n", encoding="ascii")
    observed = _read_bounded(GPU_BRIDGE / "hybrid_mode", {"0", "1"}) == "1"
    if observed != wanted_hybrid:
        raise RuntimeError("Lenovo firmware did not stage the GPU profile")
    atomic(HARDWARE_STATUS, {
        "schema": 1, "requested_gpu": profile, "previous_gpu": before["gpu_profile"],
        "set_boot_id": BOOT_ID.read_text(encoding="ascii").strip(), "reboot_required": True,
    })
    return hardware_profile_status()


def expire_pending() -> None:
    if PENDING and time.monotonic() >= float(PENDING["expires_monotonic"]): clear_pending("expired")


def capabilities() -> dict[str, object]:
    return {"schema": 1, "profile": PROFILE, "actions": ["reboot", "poweroff", "suspend"],
            "confirmation": "host-enforced-two-step", "ttl_seconds": TTL_SECONDS,
            "hardware_profiles": True, "gpu_confirmation": "host-enforced-two-step",
            "arbitrary_commands": False}


def apply(operation: str, payload: dict[str, object], peer: HostServicesPeer, shell_pid: int | None) -> dict[str, object]:
    global LAST_PREPARE, PENDING
    expire_pending()
    if operation == "capabilities.get": return capabilities()
    if operation == "system.action.status":
        return {"schema": 1, "profile": PROFILE, "pending": bool(PENDING),
                "action": PENDING.get("action") if PENDING else None, "update": update_state()}
    if operation == "hardware.profile.status": return hardware_profile_status()
    if shell_pid is None: raise PermissionError("power mutation requires a direct Quickshell action")
    if operation == "hardware.platform.set":
        profile = payload.get("profile")
        if type(profile) is not str: raise ValueError("platform profile differs")
        result = set_platform_profile(profile); audit("platform-profile", profile, "applied", peer.uid)
        return result
    if operation == "hardware.display.set":
        percent = payload.get("percent")
        if type(percent) is not int: raise ValueError("display brightness differs")
        result = set_display_brightness(percent); audit("display-brightness", str(percent), "applied", peer.uid)
        return result
    if operation == "hardware.keyboard.cycle":
        if payload: raise ValueError("keyboard backlight payload differs")
        result = cycle_keyboard_brightness()
        audit("keyboard-backlight", str(result["keyboard_brightness"]), "applied", peer.uid)
        return result
    if operation == "hardware.gpu.prepare":
        target = payload.get("profile")
        if target not in {"hybrid", "nvidia"}: raise ValueError("GPU profile differs")
        now = time.monotonic()
        if PENDING: raise RuntimeError("another confirmation is pending")
        if now - LAST_PREPARE < 2: raise RuntimeError("hardware confirmation rate limit")
        LAST_PREPARE = now; token = secrets.token_urlsafe(32)
        PENDING = {"action": "gpu", "target": target,
                   "token_digest": hashlib.sha256(token.encode()).hexdigest(),
                   "shell_pid": shell_pid, "peer_uid": peer.uid, "expires_monotonic": now + TTL_SECONDS}
        audit("gpu-prepare", str(target), "prepared", peer.uid)
        return {"prepared": True, "profile": target, "token": token, "expires_in": TTL_SECONDS,
                "reboot_required": True,
                "impact": "fecha o Environment e requer reinício para mudar o caminho físico do ecrã"}
    if operation in {"system.reboot.prepare", "system.poweroff.prepare", "system.suspend.prepare"}:
        now = time.monotonic()
        if PENDING: raise RuntimeError("another power confirmation is pending")
        if now - LAST_PREPARE < 2: raise RuntimeError("power confirmation rate limit")
        action = operation.split(".")[1]
        LAST_PREPARE = now; found = blockers(action)
        if found:
            audit("prepare", action, "blocked", peer.uid)
            return {"prepared": False, "action": action, "blockers": found,
                    "reboot_required": bool(update_state().get("reboot_required"))}
        reserve(); token = secrets.token_urlsafe(32)
        PENDING = {"action": action, "token_digest": hashlib.sha256(token.encode()).hexdigest(),
                   "shell_pid": shell_pid, "peer_uid": peer.uid, "expires_monotonic": now + TTL_SECONDS}
        atomic(STATUS, {"schema": 1, "profile": PROFILE, "state": "awaiting-confirmation", "action": action})
        audit("prepare", action, "prepared", peer.uid)
        return {"prepared": True, "action": action, "token": token, "expires_in": TTL_SECONDS,
                "impact": ("bloqueia o ecrã e suspende a máquina, mantendo o Environment"
                           if action == "suspend" else
                           "fecha o Environment ativo e atua na máquina física"),
                "blockers": [], "reboot_required": bool(update_state().get("reboot_required"))}
    token = payload.get("token")
    if type(token) is not str or not 20 <= len(token) <= 128 or not PENDING:
        raise ValueError("power confirmation token differs")
    if shell_pid != PENDING["shell_pid"] or peer.uid != PENDING["peer_uid"] \
            or not secrets.compare_digest(hashlib.sha256(token.encode()).hexdigest(), str(PENDING["token_digest"])):
        raise PermissionError("power confirmation token is not valid for this Quickshell")
    action = str(PENDING["action"])
    if action == "gpu":
        target = str(PENDING["target"])
        if operation == "hardware.gpu.cancel":
            clear_pending("cancelled"); audit("gpu-cancel", target, "cancelled", peer.uid)
            return {"cancelled": True, "profile": target}
        if operation != "hardware.gpu.confirm": raise ValueError("unsupported GPU confirmation operation")
        PENDING = None
        result = set_gpu_profile(target)
        audit("gpu-confirm", target, "staged", peer.uid)
        return result
    if operation == "system.action.cancel":
        clear_pending("cancelled"); audit("cancel", action, "cancelled", peer.uid)
        return {"cancelled": True, "action": action}
    if operation != "system.action.confirm": raise ValueError("unsupported system-power operation")
    unit = f"apx-system-power-{action}-{secrets.token_hex(6)}"
    PENDING = None
    result = subprocess.run(("/usr/bin/systemd-run", f"--unit={unit}", "--collect", "--no-block",
                             "--property=Type=oneshot", "--property=TimeoutStartSec=90s",
                             RUNNER, "--action", action), text=True, capture_output=True, check=False)
    if result.returncode:
        RESERVATION.unlink(missing_ok=True); raise RuntimeError("could not launch coordinated Host power action")
    atomic(STATUS, {"schema": 1, "profile": PROFILE, "state": "accepted", "action": action, "unit": unit + ".service"})
    audit("confirm", action, "accepted", peer.uid)
    return {"accepted": True, "action": action, "unit": unit + ".service"}


def receive(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
        chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
        if not chunk: break
        data.extend(chunk)
    return bytes(data)


def respond(connection: socket.socket) -> None:
    try:
        pid, uid, gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        peer = HostServicesPeer(pid, uid, gid); authorize_official_hub_peer(peer)
        request = parse_message(receive(connection)); operation = request.get("operation"); payload = request.get("payload")
        if type(operation) is not str or type(payload) is not dict: raise ValueError("system-power request differs")
        shell_pid = quickshell_parent(pid) if operation not in {
            "capabilities.get", "system.action.status", "hardware.profile.status",
        } else None
        with LOCK: result = apply(operation, payload, peer, shell_pid)
        response = {"schema": 1, "profile": PROFILE, "ok": True, "result": result, "error": None}
    except Exception as error:
        response = {"schema": 1, "profile": PROFILE, "ok": False, "result": None,
                    "error": {"code": "request_rejected", "message": str(error)[:300]}}
    try:
        connection.sendall((json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode())
    except BrokenPipeError:
        pass


def admit_existing_active_session() -> None:
    try:
        value = json.loads(ACTIVE.read_text()); pid = int(value["pid"])
        fields = Path(f"/proc/{pid}/uid_map").read_text().split()
        if len(fields) == 3 and fields[0] == "0" and int(fields[2]) == 65536:
            translated = int(fields[1]) + 1000; os.chown(SOCKET, translated, translated); os.chmod(SOCKET, 0o660)
    except (OSError, ValueError, KeyError, json.JSONDecodeError): pass


def serve() -> None:
    RESERVATION.unlink(missing_ok=True); SOCKET.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
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
            if endpoint == SOCKET:
                os.chmod(endpoint, 0o600)
                admit_existing_active_session()
            else:
                # The root-owned parent prevents replacement. Connection is
                # open because idmapped ownership cannot be changed without
                # CAP_CHOWN; the exact peer/cgroup checks remain authoritative.
                os.chmod(endpoint, 0o666)
            server.listen(8)
            servers.append(server)
        while True:
            readable, _, _ = select.select(servers, [], [], 1)
            if not readable:
                with LOCK: expire_pending()
                continue
            for server in readable:
                connection, _ = server.accept()
                with connection:
                    respond(connection)
    finally:
        for server in servers:
            server.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--serve", action="store_true", required=True); serve()
