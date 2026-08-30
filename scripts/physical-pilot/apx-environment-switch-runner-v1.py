#!/usr/bin/env python3
"""Host-owned supervisor for Hub -> workload -> Hub graphical handoff."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Callable


LOCK = Path("/run/apx/environment-handoff-v1.lock")
HANDOFF_PROOF = Path("/run/apx/authenticated-handoff-v1")
WORKLOAD_ACTIVE = Path("/run/apx/active-graphical-environment-v1.json")
NEXT_ENVIRONMENT = Path("/run/apx/environment-switch-next-v1.json")
HUB = "/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py"
GENERAL = "/usr/lib/apx/apx-graphical-environment-v1.py"
FAILSAFE_UNIT = "apx-environment-switch-failsafe-v1"


def transition_screen(message: str, progress: int) -> None:
    """Keep tty1 as a branded progress surface, never a visible Host prompt."""
    progress = max(0, min(100, progress))
    filled = round(30 * progress / 100)
    bar = "#" * filled + "-" * (30 - filled)
    payload = (
        "\033[2J\033[H\033[?25l\033[40m\033[96m\n\n\n\n\n\n"
        "                  APX ENVIRONMENTS\033[0m\033[40m\n\n"
        f"                  \033[97m{message}\033[0m\033[40m\n\n"
        f"                  \033[96m[{bar}]  {progress:3d}%\033[0m\033[40m\n\n"
        "                  \033[90mA tua sessão está a ser preparada.\033[0m\033[40m\n"
    ).encode()
    descriptor = os.open("/dev/tty1", os.O_WRONLY | os.O_NOCTTY)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)


def restore_console_cursor() -> None:
    try:
        descriptor = os.open("/dev/tty1", os.O_WRONLY | os.O_NOCTTY)
        try:
            os.write(descriptor, b"\033[?25h")
        finally:
            os.close(descriptor)
    except OSError:
        pass


def hide_host_getty() -> None:
    """Prevent the Host login prompt from repainting the APX transition."""
    # Stopping is not sufficient: getty.target and the Hub autostart unit may
    # immediately pull the prompt back in while a graphical handoff is still
    # running.  A runtime-only mask follows the supervised GUI chain and is
    # removed when APX genuinely returns to the Host console.
    run(("systemctl", "mask", "--runtime", "--now", "getty@tty1.service"), False)


def restore_host_getty() -> None:
    """Restore recovery login only when no newer handoff or GUI owns tty1."""
    try:
        machines = run(("machinectl", "list", "--no-legend"), False).stdout.strip()
        tty = Path("/sys/class/tty/tty0/active").read_text().strip()
        if LOCK.exists() or machines or tty != "tty1":
            return
        run(("systemctl", "unmask", "--runtime", "getty@tty1.service"), False)
        run(("systemctl", "start", "getty@tty1.service"), False)
        restore_console_cursor()
    except OSError:
        pass


def run(arguments: tuple[str, ...], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, text=True, capture_output=True, check=False,
                            env={"PATH": "/usr/bin:/usr/local/bin", "LC_ALL": "C"})
    if check and result.returncode:
        detail = (result.stderr.strip() or result.stdout.strip() or "no diagnostic output")[-2000:]
        raise RuntimeError(
            f"command failed ({result.returncode}): {arguments[0]}: {detail}"
        )
    return result


def wait_recovered() -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        machines = run(("machinectl", "list", "--no-legend"), False).stdout.strip()
        tty = Path("/sys/class/tty/tty0/active").read_text().strip()
        if not machines and tty == "tty1":
            return
        time.sleep(0.05)
    raise RuntimeError("o Environment anterior não recuperou tty1 sem resíduos")


def unlink_owned_handoff_proof(device: int, inode: int) -> None:
    try:
        metadata = HANDOFF_PROOF.lstat()
    except FileNotFoundError:
        return
    if not HANDOFF_PROOF.is_symlink() and (metadata.st_dev, metadata.st_ino) == (device, inode):
        HANDOFF_PROOF.unlink()


def release_handoff_lock(descriptor, device: int, inode: int) -> None:
    """Release only this supervisor's lock pathname.

    A restored Hub is allowed to begin the next transition while this runner
    still waits for that Hub session to end.  Inode matching prevents the old
    runner's cleanup from deleting a newer supervisor's lock.
    """
    if not descriptor.closed:
        descriptor.close()
    try:
        metadata = LOCK.lstat()
    except FileNotFoundError:
        return
    if not LOCK.is_symlink() and (metadata.st_dev, metadata.st_ino) == (device, inode):
        LOCK.unlink()


def run_authenticated(
    arguments: tuple[str, ...], message: str, start_progress: int,
    readiness: Callable[[], bool] | None = None,
    on_ready: Callable[[], None] | None = None,
) -> subprocess.CompletedProcess[str]:
    descriptor = os.open(HANDOFF_PROOF, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
    try:
        metadata = os.fstat(descriptor)
        os.write(descriptor, b"apx-authenticated-handoff-v1\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    process = subprocess.Popen(
        (*arguments, "--authenticated-handoff"), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={"PATH": "/usr/bin:/usr/local/bin", "LC_ALL": "C"},
    )
    try:
        transition_screen(message, start_progress)
        # Once systemd-nspawn has registered the destination, its read-only
        # bind mount pins the proof inode. Remove the Host pathname now so the
        # active session cannot block the next authenticated transition.
        deadline = time.monotonic() + 20
        while process.poll() is None and time.monotonic() < deadline:
            if run(("machinectl", "list", "--no-legend"), False).stdout.strip():
                transition_screen(message, min(90, start_progress + 18))
                break
            time.sleep(0.05)
        unlink_owned_handoff_proof(metadata.st_dev, metadata.st_ino)
        if readiness is not None:
            while process.poll() is None and time.monotonic() < deadline:
                if readiness():
                    if on_ready is not None:
                        on_ready()
                    break
                time.sleep(0.05)
        stdout, stderr = process.communicate()
        result = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
        if result.returncode:
            detail = (result.stderr.strip() or result.stdout.strip() or "no diagnostic output")[-2000:]
            raise RuntimeError(f"command failed ({result.returncode}): {arguments[0]}: {detail}")
        return result
    finally:
        unlink_owned_handoff_proof(metadata.st_dev, metadata.st_ino)


def arm_failsafe(name: str, seconds: int = 120) -> None:
    run(("systemctl", "stop", FAILSAFE_UNIT + ".timer", FAILSAFE_UNIT + ".service"), False)
    result = run((
        "systemd-run", f"--unit={FAILSAFE_UNIT}", f"--on-active={seconds}s",
        "--timer-property=AccuracySec=1s", GENERAL, "--environment", name, "--recover",
    ), False)
    if result.returncode:
        raise RuntimeError(f"não foi possível armar o regresso automático: {result.stderr.strip()}")


def disarm_failsafe() -> None:
    run(("systemctl", "stop", FAILSAFE_UNIT + ".timer", FAILSAFE_UNIT + ".service"), False)


def workload_ready(name: str) -> bool:
    """Accept only the root-published, generation-bound healthy workload state."""
    registration = Path("/var/lib/apx/environments") / name / "registration.json"
    try:
        active_metadata = WORKLOAD_ACTIVE.lstat()
        registration_metadata = registration.lstat()
        active_data = WORKLOAD_ACTIVE.read_bytes()
        registration_data = registration.read_bytes()
        active = json.loads(active_data)
        record = json.loads(registration_data)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return False
    if WORKLOAD_ACTIVE.is_symlink() or registration.is_symlink() \
            or not WORKLOAD_ACTIVE.is_file() or not registration.is_file() \
            or (active_metadata.st_uid, active_metadata.st_gid) != (0, 0) \
            or (registration_metadata.st_uid, registration_metadata.st_gid) != (0, 0) \
            or len(active_data) > 2048 or len(registration_data) > 8192 \
            or type(active) is not dict or type(record) is not dict:
        return False
    generation = record.get("generation")
    expected_unit = f"apx-graphical-{name}-{str(generation)[:8]}.service"
    return (record.get("name"), record.get("role"), record.get("release"), record.get("state")) == (
        name, "graphical-base", "hyprland-base-v2", "running",
    ) and (active.get("profile"), active.get("name"), active.get("role"),
           active.get("generation"), active.get("unit")) == (
        "apx-active-graphical-environment-v1", name, "graphical-base", generation, expected_unit,
    ) and type(active.get("pid")) is int and active["pid"] > 1


def consume_next_environment(source: str) -> str | None:
    try:
        metadata = NEXT_ENVIRONMENT.lstat()
        data = NEXT_ENVIRONMENT.read_bytes()
    except FileNotFoundError:
        return None
    if NEXT_ENVIRONMENT.is_symlink() or not NEXT_ENVIRONMENT.is_file() \
            or (metadata.st_uid, metadata.st_gid) != (0, 0) \
            or len(data) > 2048:
        raise RuntimeError("o pedido de troca direta não é confiável")
    try:
        value = json.loads(data)
    finally:
        current = NEXT_ENVIRONMENT.lstat()
        if (current.st_dev, current.st_ino) == (metadata.st_dev, metadata.st_ino):
            NEXT_ENVIRONMENT.unlink()
    if set(value) != {"schema", "profile", "source", "target", "generation"} \
            or value.get("schema") != 1 or value.get("profile") != "apx-environment-next-v1" \
            or value.get("source") != source:
        raise RuntimeError("a identidade da troca direta difere")
    target, generation = value.get("target"), value.get("generation")
    if type(target) is not str or re.fullmatch(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}", target) is None \
            or target in {"hub", source} or type(generation) is not str:
        raise RuntimeError("o destino da troca direta difere")
    registration = Path("/var/lib/apx/environments") / target / "registration.json"
    try:
        registration_metadata = registration.lstat()
        registration_data = registration.read_bytes()
        record = json.loads(registration_data)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as error:
        raise RuntimeError("o registo do destino da troca direta não é confiável") from error
    if registration.is_symlink() or not registration.is_file() \
            or (registration_metadata.st_uid, registration_metadata.st_gid) != (0, 0) \
            or len(registration_data) > 8192 or type(record) is not dict:
        raise RuntimeError("o registo do destino da troca direta não é confiável")
    if (record.get("name"), record.get("role"), record.get("release"),
            record.get("generation"), record.get("state")) != (
        target, "graphical-base", "hyprland-base-v2", generation, "stopped",
    ):
        raise RuntimeError("o destino da troca direta mudou")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--environment")
    mode.add_argument("--relaunch-hub", action="store_true")
    arguments = parser.parse_args(); name = arguments.environment
    if not arguments.relaunch_hub and (type(name) is not str \
            or re.fullmatch(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}", name) is None or name == "hub"):
        parser.error("invalid graphical Environment")
    descriptor = LOCK.open("x")
    lock_metadata = os.fstat(descriptor.fileno())
    owns_transition = True
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        hide_host_getty()
        transition_screen("A FECHAR O HUB", 8)
        run((HUB, "--recover")); wait_recovered()
        transition_screen("A PREPARAR O NOVO ENVIRONMENT", 38)
        if arguments.relaunch_hub:
            release_handoff_lock(descriptor, lock_metadata.st_dev, lock_metadata.st_ino)
            owns_transition = False
            run_authenticated((HUB, "--interactive"), "A ABRIR O HUB", 68)
            return 0
        workload_failure: Exception | None = None
        assert name is not None
        while True:
            try:
                arm_failsafe(name)
                run_authenticated((GENERAL, "--environment", name, "--interactive"),
                                  "A ABRIR " + name.upper(), 62,
                                  readiness=lambda: workload_ready(name),
                                  on_ready=disarm_failsafe)
            except Exception as error:
                workload_failure = error
            finally:
                disarm_failsafe()
                transition_screen("A FECHAR " + name.upper(), 34)
                run((GENERAL, "--environment", name, "--recover"), False)
                try:
                    wait_recovered()
                except Exception as error:
                    if workload_failure is None:
                        workload_failure = error
                    else:
                        print(f"APX workload recovery also failed: {error}", file=sys.stderr, flush=True)
            try:
                next_name = consume_next_environment(name)
            except Exception as error:
                # A malformed or stale direct-switch request must never strand
                # the owner at tty1.  Preserve the failure and follow the same
                # guaranteed Hub-restoration path used for workload failures.
                next_name = None
                if workload_failure is None:
                    workload_failure = error
                else:
                    print(f"APX direct switch also failed: {error}", file=sys.stderr, flush=True)
            if workload_failure is not None or next_name is None:
                break
            name = next_name
            transition_screen("A TROCAR PARA " + name.upper(), 48)
        transition_screen("A ABRIR O HUB", 64)
        release_handoff_lock(descriptor, lock_metadata.st_dev, lock_metadata.st_ino)
        owns_transition = False
        try:
            run_authenticated((HUB, "--interactive"), "A ABRIR O HUB", 76)
        except Exception as error:
            if workload_failure is not None:
                raise RuntimeError(
                    f"o destino falhou ({workload_failure}) e o regresso ao HUB também falhou ({error})"
                ) from error
            raise
        if workload_failure is not None:
            raise RuntimeError(
                f"o destino falhou, mas o HUB foi restaurado: {workload_failure}"
            ) from workload_failure
    except Exception as error:
        print(f"APX Environment handoff failed: {error}", file=sys.stderr, flush=True)
        raise
    finally:
        if owns_transition:
            disarm_failsafe()
            release_handoff_lock(descriptor, lock_metadata.st_dev, lock_metadata.st_ino)
        restore_host_getty()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
