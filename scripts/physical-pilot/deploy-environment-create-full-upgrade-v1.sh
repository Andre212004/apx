#!/usr/bin/bash
set -euo pipefail

# Exact physical-pilot repair for Arch's unsupported partial-upgrade boundary.
# It replaces only the shared APX lifecycle runtime and never starts, creates,
# cleans, or destroys an Environment.
readonly repository=/root/apx-host-development-mode-v1/apx
readonly source_runtime="$repository/scripts/virtual-lab/apx-lab-runtime.py"
readonly target_runtime=/usr/lib/apx/apx-lab-runtime.py
readonly command_link=/usr/bin/apx
readonly backup=/var/lib/apx/backups/20260825-environment-create-full-upgrade-v1

fail() { /usr/bin/printf 'APX Environment creation repair refused: %s\n' "$1" >&2; exit 2; }

[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot \
    || fail "physical-pilot marker differs"
[[ $PWD == "$repository" ]] || fail "run from the dedicated repository"
[[ ! -e $backup ]] || fail "backup destination already exists"
[[ -f $source_runtime && ! -L $source_runtime ]] || fail "source runtime differs"
[[ -f $target_runtime && ! -L $target_runtime ]] || fail "installed runtime differs"
[[ -L $command_link && $(/usr/bin/readlink -f "$command_link") == "$target_runtime" ]] \
    || fail "APX command link differs"
[[ $(/usr/bin/machinectl list --no-legend | /usr/bin/awk '{print $1}') == apx-hub ]] \
    || fail "the Hub is not the only active machine"
! /usr/bin/pgrep -f '^/usr/lib/apx/apx-environment-management-runner-v1.py ' >/dev/null \
    || fail "Environment management is active"

/usr/bin/python3 -m unittest discover -s tests >/dev/null \
    || fail "repository tests failed"
/usr/bin/python3 -m py_compile "$source_runtime" \
    || fail "source runtime does not compile"
/usr/bin/grep -Fq '"--disable-sandbox", "-Syu", "--needed", "--noconfirm"' "$source_runtime" \
    || fail "complete-upgrade command is absent"
! /usr/bin/grep -Fq '"--disable-sandbox", "-Sy", "--needed", "--noconfirm"' "$source_runtime" \
    || fail "partial-upgrade command remains"

/usr/bin/install -d -m 0700 "$backup"
/usr/bin/cp --archive -- "$target_runtime" "$backup/apx-lab-runtime.py"
/usr/bin/sha256sum "$target_runtime" >"$backup/before.sha256"

temporary="${target_runtime}.apx-full-upgrade.$$"
rollback() {
    trap - ERR
    /usr/bin/rm -f -- "$temporary"
    /usr/bin/cp --archive -- "$backup/apx-lab-runtime.py" "$target_runtime"
    fail "installation failed; the exact previous runtime was restored"
}
trap rollback ERR

/usr/bin/install -m 0755 -o root -g root -- "$source_runtime" "$temporary"
/usr/bin/mv -Tf -- "$temporary" "$target_runtime"
/usr/bin/cmp -s -- "$source_runtime" "$target_runtime"
/usr/bin/cmp -s -- "$source_runtime" "$command_link"

trap - ERR
/usr/bin/sha256sum "$target_runtime" >"$backup/after.sha256"
/usr/bin/chmod 0600 "$backup/before.sha256" "$backup/after.sha256"
/usr/bin/printf 'APX Environment creation full-upgrade repair installed; rollback: %s\n' "$backup"
