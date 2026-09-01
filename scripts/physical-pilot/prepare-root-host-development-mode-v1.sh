#!/usr/bin/env bash
set -euo pipefail

readonly EXPECTED_HOSTNAME="apx-host"
readonly EXPECTED_VENDOR="LENOVO"
readonly EXPECTED_PRODUCT="82JU"
readonly EXPECTED_BOARD="LNVNB161216"
readonly EXPECTED_PROFILE="profile=apx-physical-headless-pilot-v1"
readonly MODE_ROOT="/root/apx-host-development-mode-v1"
readonly REPOSITORY_ROOT="${MODE_ROOT}/apx"
readonly EVIDENCE_ROOT="${MODE_ROOT}/evidence"
readonly INSTALLER="/tmp/apx-codex-install-v1.sh"
readonly REPOSITORY_URL="https://github.com/andrepereira2004/apx.git"
readonly APPROVAL="ENABLE TEMPORARY ROOT CODEX ON APX-HOST"

fail() {
  printf 'BLOCKED: %s\n' "$*" >&2
  exit 1
}

read_one_line() {
  local path="$1"
  test -r "$path" || fail "cannot read required identity path: $path"
  sed -n '1p' "$path"
}

test "$(id -u)" -eq 0 || fail "run only as root on the physical host console"
test "$(hostnamectl --static)" = "$EXPECTED_HOSTNAME" || fail "hostname mismatch"
detected_virtualization="$(systemd-detect-virt 2>/dev/null || true)"
test "$detected_virtualization" = "none" || fail "physical-host check failed"
test "$(read_one_line /sys/class/dmi/id/sys_vendor)" = "$EXPECTED_VENDOR" || fail "vendor mismatch"
test "$(read_one_line /sys/class/dmi/id/product_name)" = "$EXPECTED_PRODUCT" || fail "product mismatch"
test "$(read_one_line /sys/class/dmi/id/board_name)" = "$EXPECTED_BOARD" || fail "board mismatch"
grep -Fxq "$EXPECTED_PROFILE" /etc/apx-physical-pilot || fail "pilot marker mismatch"
test -d /var/lib/apx || fail "APX state root is absent"
command -v apx >/dev/null || fail "APX command is absent"
command -v curl >/dev/null || fail "curl is required to fetch the reviewed Codex installer"

printf 'Identity accepted: root@%s, %s %s %s\n' \
  "$EXPECTED_HOSTNAME" "$EXPECTED_VENDOR" "$EXPECTED_PRODUCT" "$EXPECTED_BOARD"
printf 'This mode gives Codex full technical control of the disposable pilot.\n'
printf 'Type exactly: %s\n> ' "$APPROVAL"
IFS= read -r typed_approval
test "$typed_approval" = "$APPROVAL" || fail "approval mismatch"

install -d -m 700 "$MODE_ROOT" "$EVIDENCE_ROOT"

{
  printf 'captured_at=%s\n' "$(date --iso-8601=seconds)"
  printf 'hostname=%s\n' "$(hostnamectl --static)"
  printf 'vendor=%s\n' "$(read_one_line /sys/class/dmi/id/sys_vendor)"
  printf 'product=%s\n' "$(read_one_line /sys/class/dmi/id/product_name)"
  printf 'board=%s\n' "$(read_one_line /sys/class/dmi/id/board_name)"
  printf 'git_before=%s\n' "$(command -v git 2>/dev/null || printf absent)"
  printf 'gh_before=%s\n' "$(command -v gh 2>/dev/null || printf absent)"
  printf 'codex_before=%s\n' "$(command -v codex 2>/dev/null || printf absent)"
} >"${EVIDENCE_ROOT}/baseline.txt"
chmod 600 "${EVIDENCE_ROOT}/baseline.txt"

missing_packages=()
pacman -Q git >/dev/null 2>&1 || missing_packages+=(git)
pacman -Q github-cli >/dev/null 2>&1 || missing_packages+=(github-cli)
if ((${#missing_packages[@]})); then
  pacman -S --needed "${missing_packages[@]}"
fi

if ! test -d "${REPOSITORY_ROOT}/.git"; then
  test ! -e "$REPOSITORY_ROOT" || fail "repository target exists but is not a Git checkout"
  git clone --branch master --single-branch "$REPOSITORY_URL" "$REPOSITORY_ROOT"
fi
test "$(git -C "$REPOSITORY_ROOT" remote get-url origin)" = "$REPOSITORY_URL" || fail "repository origin mismatch"

if ! command -v codex >/dev/null; then
  curl -fsSL https://chatgpt.com/codex/install.sh -o "$INSTALLER"
  chmod 700 "$INSTALLER"
  sha256sum "$INSTALLER" | tee "${EVIDENCE_ROOT}/codex-installer.sha256"
  sed -n '1,260p' "$INSTALLER"
  printf '\nReview the installer above. Type exactly: RUN REVIEWED CODEX INSTALLER\n> '
  IFS= read -r installer_approval
  test "$installer_approval" = "RUN REVIEWED CODEX INSTALLER" || fail "installer approval mismatch"
  sh "$INSTALLER"
  rm -f -- "$INSTALLER"
fi

command -v git
command -v gh
command -v codex
git -C "$REPOSITORY_ROOT" status --short --branch

printf '\nPreparation complete. Next run:\n'
printf '  gh auth login\n'
printf '  codex login --device-auth\n'
printf '  cd %s\n' "$REPOSITORY_ROOT"
printf '  codex\n'
printf 'Then paste the prompt from docs/temporary-root-host-development-mode-v1.md.\n'
