#!/usr/bin/bash
set -euo pipefail

# Target-bound adapter only. AGENTS.md permits execution on the disposable
# physical pilot solely when the owner explicitly invokes the temporary Host
# development guide as root@apx-host. Repository work must not run this file.
readonly repository=/root/apx-host-development-mode-v1/apx
readonly backup=/var/lib/apx/backups/20260824-system-vm-v2-v20
readonly template=/usr/lib/apx/system-environment-template-v2
readonly environments=/var/lib/apx/environments

fail() { /usr/bin/printf 'APX VM v2 deployment refused: %s\n' "$1" >&2; exit 2; }

[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot \
    || fail "physical-pilot marker differs"
[[ $PWD == "$repository" ]] || fail "run from the dedicated repository"
[[ ! -e $backup ]] || fail "backup destination already exists"
[[ ! -e /run/apx/vfio-pci-environment-v1.json ]] || fail "VFIO is active"
! /usr/bin/pgrep -x qemu-system-x86 >/dev/null || fail "QEMU is active"
! /usr/bin/pgrep -x looking-glass-c >/dev/null || fail "Looking Glass is active"
[[ $(/usr/bin/machinectl list --no-legend | /usr/bin/awk '{print $1}') == apx-hub ]] \
    || fail "the Hub is not the only active machine"

/usr/bin/python3 -m unittest discover -s tests >/dev/null \
    || fail "repository tests failed"

system_rows=$(/usr/bin/python3 - "$environments" <<'PY'
import json
from pathlib import Path
import sys

for environment in sorted(Path(sys.argv[1]).iterdir()):
    marker = environment / "system-environment-v1.json"
    if not marker.is_file():
        continue
    registration = json.loads((environment / "registration.json").read_text())
    metadata = json.loads(marker.read_text())
    if registration.get("state") != "stopped":
        raise SystemExit(f"{environment.name} is not stopped")
    kind = metadata.get("system_kind")
    if kind not in {"windows11", "ubuntu"}:
        raise SystemExit(f"{environment.name} has an unsupported system kind")
    print(f"{environment.name}:{kind}")
PY
)
system_environments=()
if [[ -n $system_rows ]]; then
    mapfile -t system_environments <<<"$system_rows"
fi

targets=(
    /usr/lib/apx/apx-graphical-environment-v1.py
    /usr/lib/apx/apx-system-environment-provision-v1.py
    "$template/local/bin/apx-vm-runtime-v2"
    "$template/profiles/windows11.json"
    "$template/profiles/ubuntu.json"
    "$template/hypr/hyprland.lua"
    "$template/vfio-pci-v1.json"
)
for asset in ATIVAR-ACELERACAO.cmd APX-CONFIGURAR-120HZ.ps1 LEIA-ME.txt; do
    targets+=("$template/APXTools/$asset")
done
for entry in "${system_environments[@]}"; do
    name=${entry%%:*}; kind=${entry#*:}; home="$environments/$name/home/apx"
    targets+=(
        "$home/.local/bin/apx-system-vm"
        "$home/.config/apx/system-vm-v2.json"
        "$home/.config/hypr/hyprland.lua"
        "$home/.local/state/apx-system-vm-v2/presentation"
    )
    if [[ $kind == windows11 ]]; then
        for asset in ATIVAR-ACELERACAO.cmd APX-CONFIGURAR-120HZ.ps1 LEIA-ME.txt; do
            targets+=("$home/APXTools/$asset")
        done
    fi
done

/usr/bin/install -d -m 0700 "$backup"
for target in "${targets[@]}"; do
    if [[ -e $target ]]; then
        /usr/bin/cp --archive --parents -- "$target" "$backup"
    else
        /usr/bin/printf '%s\n' "$target" >>"$backup/created-paths.txt"
    fi
done
/usr/bin/sha256sum "${targets[@]}" 2>/dev/null >"$backup/before.sha256" || true

atomic_install() {
    local source=$1 target=$2 mode=$3 owner=$4 group=$5 temporary
    temporary="${target}.apx-v2.$$"
    /usr/bin/install -D -m "$mode" -o "$owner" -g "$group" -- "$source" "$temporary"
    /usr/bin/mv -Tf -- "$temporary" "$target"
}

rollback() {
    local target saved directory uid gid mode
    trap - ERR
    for target in "${targets[@]}"; do
        saved="$backup$target"
        if [[ -e $saved ]]; then
            /usr/bin/cp --archive -- "$saved" "$target"
        else
            /usr/bin/rm -f -- "$target"
        fi
    done
    if [[ -f $backup/nocow-added.txt ]]; then
        while IFS= read -r directory; do
            /usr/bin/chattr -C "$directory" || true
        done <"$backup/nocow-added.txt"
    fi
    if [[ -f $backup/user-directory-metadata.before ]]; then
        while IFS=' ' read -r uid gid mode directory; do
            /usr/bin/chown "$uid:$gid" "$directory" || true
            /usr/bin/chmod "$mode" "$directory" || true
        done <"$backup/user-directory-metadata.before"
    fi
    fail "installation failed; exact previous files were restored"
}
trap rollback ERR

atomic_install scripts/physical-pilot/apx-graphical-environment-v1.py \
    /usr/lib/apx/apx-graphical-environment-v1.py 0755 root root
atomic_install scripts/physical-pilot/apx-system-environment-provision-v1.py \
    /usr/lib/apx/apx-system-environment-provision-v1.py 0755 root root
atomic_install config/environment-vm-v2/local/bin/apx-vm-runtime-v2 \
    "$template/local/bin/apx-vm-runtime-v2" 0755 root root
for kind in windows11 ubuntu; do
    atomic_install "config/environment-vm-v2/profiles/$kind.json" \
        "$template/profiles/$kind.json" 0644 root root
done
atomic_install config/environment-vm-v2/hypr/hyprland.lua \
    "$template/hypr/hyprland.lua" 0644 root root
atomic_install config/environment-vm-v2/vfio-pci-v1.json \
    "$template/vfio-pci-v1.json" 0400 root root
for asset in ATIVAR-ACELERACAO.cmd APX-CONFIGURAR-120HZ.ps1 LEIA-ME.txt; do
    atomic_install "config/environment-vm-v2/APXTools/$asset" \
        "$template/APXTools/$asset" 0444 root root
done

for entry in "${system_environments[@]}"; do
    name=${entry%%:*}; kind=${entry#*:}; home="$environments/$name/home/apx"
    for directory in "$home/.config" "$home/.config/apx" "$home/.config/hypr" \
            "$home/.local" "$home/.local/bin"; do
        /usr/bin/stat -Lc '%u %g %a %n' "$directory" >>"$backup/user-directory-metadata.before"
        /usr/bin/install -d -m 0700 -o 1000 -g 1000 "$directory"
    done
    atomic_install config/environment-vm-v2/local/bin/apx-vm-runtime-v2 \
        "$home/.local/bin/apx-system-vm" 0755 1000 1000
    atomic_install "config/environment-vm-v2/profiles/$kind.json" \
        "$home/.config/apx/system-vm-v2.json" 0600 1000 1000
    atomic_install config/environment-vm-v2/hypr/hyprland.lua \
        "$home/.config/hypr/hyprland.lua" 0600 1000 1000
    /usr/bin/install -d -m 0700 -o 1000 -g 1000 "$home/.local/state/apx-system-vm-v2"
    /usr/bin/printf 'direct\n' >"$home/.local/state/apx-system-vm-v2/presentation.apx-v2.$$"
    /usr/bin/chown 1000:1000 "$home/.local/state/apx-system-vm-v2/presentation.apx-v2.$$"
    /usr/bin/chmod 0600 "$home/.local/state/apx-system-vm-v2/presentation.apx-v2.$$"
    /usr/bin/mv -Tf "$home/.local/state/apx-system-vm-v2/presentation.apx-v2.$$" \
        "$home/.local/state/apx-system-vm-v2/presentation"
    if [[ $kind == windows11 ]]; then
        for asset in ATIVAR-ACELERACAO.cmd APX-CONFIGURAR-120HZ.ps1 LEIA-ME.txt; do
            atomic_install "config/environment-vm-v2/APXTools/$asset" \
                "$home/APXTools/$asset" 0444 1000 1000
        done
    fi
    vm_dir="$home/VMs/$([[ $kind == windows11 ]] && /usr/bin/printf Windows11 || /usr/bin/printf Ubuntu)"
    raw_disk="$vm_dir/$([[ $kind == windows11 ]] && /usr/bin/printf Windows11.raw || /usr/bin/printf Ubuntu.raw)"
    legacy_disk="$vm_dir/$([[ $kind == windows11 ]] && /usr/bin/printf Windows11.qcow2 || /usr/bin/printf Ubuntu.qcow2)"
    if [[ -d $vm_dir && ! -e $raw_disk && ! -e $legacy_disk ]] \
            && [[ $(/usr/bin/lsattr -d "$vm_dir" | /usr/bin/awk '{print $1}') != *C* ]]; then
        /usr/bin/printf '%s\n' "$vm_dir" >>"$backup/nocow-added.txt"
        /usr/bin/chattr +C "$vm_dir"
    fi
done

trap - ERR
/usr/bin/sha256sum "${targets[@]}" >"$backup/after.sha256"
/usr/bin/chmod 0600 "$backup/before.sha256" "$backup/after.sha256"
[[ ! -e $backup/created-paths.txt ]] || /usr/bin/chmod 0600 "$backup/created-paths.txt"
[[ ! -e $backup/nocow-added.txt ]] || /usr/bin/chmod 0600 "$backup/nocow-added.txt"
[[ ! -e $backup/user-directory-metadata.before ]] \
    || /usr/bin/chmod 0600 "$backup/user-directory-metadata.before"

/usr/bin/cmp -s scripts/physical-pilot/apx-graphical-environment-v1.py \
    /usr/lib/apx/apx-graphical-environment-v1.py || fail "Host launcher verification failed"
for entry in "${system_environments[@]}"; do
    name=${entry%%:*}; home="$environments/$name/home/apx"
    /usr/bin/cmp -s config/environment-vm-v2/local/bin/apx-vm-runtime-v2 \
        "$home/.local/bin/apx-system-vm" || fail "$name runtime verification failed"
done

/usr/bin/printf 'APX system VM v2 installed without starting a VM; rollback: %s\n' "$backup"
