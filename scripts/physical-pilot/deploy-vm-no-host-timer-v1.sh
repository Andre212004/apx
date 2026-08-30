#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly backup=/var/lib/apx/backups/20260824-vm-no-host-timer-v14
readonly environments=/var/lib/apx/environments
readonly template=/usr/lib/apx/system-environment-template-v1

fail() { printf 'APX no-timer VM deployment refused: %s\n' "$1" >&2; exit 2; }

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
    print(json.load(stream).get("state", ""))
PY
)
    [[ $state == stopped ]] || fail "$name is not stopped"
done

targets=(
    /usr/lib/apx/apx-graphical-environment-v1.py
    "$template/local/bin/apx-windows11-vm"
)
for name in faculdade trabalho; do
    targets+=(
        "$environments/$name/home/apx/.local/bin/apx-windows11-vm"
        "$environments/$name/home/apx/.local/bin/apx-system-vm"
    )
done

/usr/bin/install -d -m 0700 "$backup"
for target in "${targets[@]}"; do
    /usr/bin/cp --archive --parents -- "$target" "$backup"
done
/usr/bin/sha256sum "${targets[@]}" >"$backup/before.sha256"

atomic_install() {
    local source=$1 target=$2 owner=$3 group=$4 temporary
    temporary="${target}.apx-v14.$$"
    /usr/bin/install -D -m 0755 -o "$owner" -g "$group" -- "$source" "$temporary"
    /usr/bin/mv -Tf -- "$temporary" "$target"
}

rollback() {
    local target
    trap - ERR
    for target in "${targets[@]}"; do
        /usr/bin/cp --archive -- "$backup$target" "$target"
    done
    fail "installation failed; exact previous files were restored"
}
trap rollback ERR

atomic_install scripts/physical-pilot/apx-graphical-environment-v1.py \
    /usr/lib/apx/apx-graphical-environment-v1.py root root
atomic_install config/environment-vm-v1/local/bin/apx-windows11-vm \
    "$template/local/bin/apx-windows11-vm" root root
for name in faculdade trabalho; do
    atomic_install config/environment-vm-v1/local/bin/apx-windows11-vm \
        "$environments/$name/home/apx/.local/bin/apx-windows11-vm" 1000 1000
    atomic_install config/environment-vm-v1/local/bin/apx-windows11-vm \
        "$environments/$name/home/apx/.local/bin/apx-system-vm" 1000 1000
done

for target in /usr/lib/apx/apx-graphical-environment-v1.py; do
    /usr/bin/cmp -s scripts/physical-pilot/apx-graphical-environment-v1.py "$target" \
        || fail "Host verifier differs"
done
for target in "$template/local/bin/apx-windows11-vm"; do
    /usr/bin/cmp -s config/environment-vm-v1/local/bin/apx-windows11-vm "$target" \
        || fail "template launcher differs"
done
for name in faculdade trabalho; do
    /usr/bin/cmp -s config/environment-vm-v1/local/bin/apx-windows11-vm \
        "$environments/$name/home/apx/.local/bin/apx-system-vm" \
        || fail "$name launcher differs"
done

trap - ERR
/usr/bin/sha256sum "${targets[@]}" >"$backup/after.sha256"
/usr/bin/chmod 0600 "$backup/before.sha256" "$backup/after.sha256"
/usr/bin/printf 'APX VM Host timer removed; rollback: %s\n' "$backup"
