#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly backup=/var/lib/apx/backups/20260824-vm-readiness-performance-v9
readonly template=/usr/lib/apx/system-environment-template-v1
readonly environments=/var/lib/apx/environments

fail() { printf 'APX VM deployment refused: %s\n' "$1" >&2; exit 2; }

[[ $(id -u) == 0 ]] || fail "root is required"
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

for name in faculdade trabalho; do
    state=$(/usr/bin/python3 - "$environments/$name/registration.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as stream:
    value = json.load(stream)
print(value.get("state", ""))
PY
)
    [[ $state == stopped ]] || fail "$name is not stopped"
done

/usr/bin/install -d -m 0700 "$backup"

targets=(
    /usr/lib/apx/apx-graphical-environment-v1.py
    /usr/lib/apx/apx-official-hub-graphical-v1.py
    /var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py
    /usr/lib/apx/apx-system-environment-provision-v1.py
    "$template/local/bin/apx-windows11-vm"
    "$template/local/bin/apx-ubuntu-vm"
    "$template/APXTools/ATIVAR-ACELERACAO.cmd"
    "$template/APXTools/LEIA-ME.txt"
    "$template/APXTools/APX-CONFIGURAR-120HZ.ps1"
)
for name in faculdade trabalho; do
    targets+=(
        "$environments/$name/home/apx/.local/bin/apx-windows11-vm"
        "$environments/$name/home/apx/.local/bin/apx-system-vm"
        "$environments/$name/home/apx/APXTools/ATIVAR-ACELERACAO.cmd"
        "$environments/$name/home/apx/APXTools/LEIA-ME.txt"
        "$environments/$name/home/apx/APXTools/APX-CONFIGURAR-120HZ.ps1"
    )
done

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
    temporary="${target}.apx-v9.$$"
    /usr/bin/install -D -m "$mode" -o "$owner" -g "$group" -- "$source" "$temporary"
    /usr/bin/mv -Tf -- "$temporary" "$target"
}

rollback() {
    local target saved
    trap - ERR
    for target in "${targets[@]}"; do
        saved="$backup$target"
        if [[ -e $saved ]]; then
            /usr/bin/cp --archive -- "$saved" "$target"
        elif [[ $target == */APX-CONFIGURAR-120HZ.ps1 ]]; then
            /usr/bin/rm -f -- "$target"
        fi
    done
    fail "installation failed; exact previous files were restored"
}
trap rollback ERR

atomic_install scripts/physical-pilot/apx-graphical-environment-v1.py \
    /usr/lib/apx/apx-graphical-environment-v1.py 0755 root root
for target in /usr/lib/apx/apx-official-hub-graphical-v1.py \
        /var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py; do
    atomic_install scripts/physical-pilot/apx-official-hub-graphical-v1.py \
        "$target" 0755 root root
done
atomic_install scripts/physical-pilot/apx-system-environment-provision-v1.py \
    /usr/lib/apx/apx-system-environment-provision-v1.py 0755 root root
atomic_install config/environment-vm-v1/local/bin/apx-windows11-vm \
    "$template/local/bin/apx-windows11-vm" 0755 root root
atomic_install config/environment-vm-v1/local/bin/apx-ubuntu-vm \
    "$template/local/bin/apx-ubuntu-vm" 0755 root root
for asset in ATIVAR-ACELERACAO.cmd LEIA-ME.txt APX-CONFIGURAR-120HZ.ps1; do
    atomic_install "config/environment-vm-v1/APXTools/$asset" \
        "$template/APXTools/$asset" 0444 root root
done

for name in faculdade trabalho; do
    atomic_install config/environment-vm-v1/local/bin/apx-windows11-vm \
        "$environments/$name/home/apx/.local/bin/apx-windows11-vm" 0755 1000 1000
    atomic_install config/environment-vm-v1/local/bin/apx-windows11-vm \
        "$environments/$name/home/apx/.local/bin/apx-system-vm" 0755 1000 1000
    for asset in ATIVAR-ACELERACAO.cmd LEIA-ME.txt APX-CONFIGURAR-120HZ.ps1; do
        atomic_install "config/environment-vm-v1/APXTools/$asset" \
            "$environments/$name/home/apx/APXTools/$asset" 0444 1000 1000
    done
done

trap - ERR
/usr/bin/sha256sum "${targets[@]}" >"$backup/after.sha256"
/usr/bin/chmod 0600 "$backup/before.sha256" "$backup/after.sha256"
[[ ! -e $backup/created-paths.txt ]] || /usr/bin/chmod 0600 "$backup/created-paths.txt"

for target in /usr/lib/apx/apx-graphical-environment-v1.py; do
    /usr/bin/cmp -s scripts/physical-pilot/apx-graphical-environment-v1.py "$target" \
        || fail "graphical launcher verification failed"
done
for target in /usr/lib/apx/apx-official-hub-graphical-v1.py \
        /var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py; do
    /usr/bin/cmp -s scripts/physical-pilot/apx-official-hub-graphical-v1.py "$target" \
        || fail "graphical engine verification failed"
done
for name in faculdade trabalho; do
    /usr/bin/cmp -s config/environment-vm-v1/local/bin/apx-windows11-vm \
        "$environments/$name/home/apx/.local/bin/apx-system-vm" \
        || fail "$name launcher verification failed"
done

/usr/bin/printf 'APX VM candidate installed; rollback: %s\n' "$backup"
