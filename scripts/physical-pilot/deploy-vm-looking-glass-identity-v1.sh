#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly source_file=$repository/scripts/physical-pilot/apx-graphical-environment-v1.py
readonly target_file=/usr/lib/apx/apx-graphical-environment-v1.py
readonly backup=/var/lib/apx/backups/20260824-vm-looking-glass-identity-v11

fail() { printf 'APX Looking Glass identity deployment refused: %s\n' "$1" >&2; exit 2; }

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

/usr/bin/install -d -m 0700 "$backup"
/usr/bin/cp --archive --parents -- "$target_file" "$backup"
/usr/bin/sha256sum "$target_file" >"$backup/before.sha256"

temporary="${target_file}.apx-v11.$$"
rollback() {
    trap - ERR
    /usr/bin/rm -f -- "$temporary"
    /usr/bin/cp --archive -- "$backup$target_file" "$target_file"
    fail "installation failed; the exact previous launcher was restored"
}
trap rollback ERR

/usr/bin/install -D -m 0755 -o root -g root -- "$source_file" "$temporary"
/usr/bin/mv -Tf -- "$temporary" "$target_file"
/usr/bin/cmp -s -- "$source_file" "$target_file" \
    || fail "installed launcher differs from the candidate"

trap - ERR
/usr/bin/sha256sum "$target_file" >"$backup/after.sha256"
/usr/bin/chmod 0600 "$backup/before.sha256" "$backup/after.sha256"
/usr/bin/printf 'APX Looking Glass identity correction installed; rollback: %s\n' "$backup"
