#!/usr/bin/env bash

set -euo pipefail
export LC_ALL=C

readonly SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly REPOSITORY=$(cd -- "$SCRIPT_DIR/../.." && pwd)
readonly STATE=/var/lib/apx
readonly RUNTIME_SOURCE=$REPOSITORY/scripts/virtual-lab/apx-lab-runtime.py
readonly CLIENT_SOURCE=$REPOSITORY/scripts/virtual-lab/apx-lab-client.py
readonly EXECUTOR_SOURCE=$REPOSITORY/scripts/virtual-lab/apx-lab-executor.py
readonly INCOMPLETE_DEVELOPMENT_RELEASE=$STATE/releases/development-headless-v1
readonly RECOVERY_APPROVAL='DELETE-INCOMPLETE-development-headless-v1'

fail() {
  printf 'APX physical bootstrap refused: %s\n' "$*" >&2
  exit 1
}

verify_physical_target() {
[[ $(id -u) == 0 ]] || fail 'host root is required'
[[ $(systemd-detect-virt) == none ]] || fail 'physical-machine pilot required'
[[ $(< /etc/hostname) == apx-host ]] || fail 'wrong host identity'
[[ -f /etc/apx-physical-pilot ]] || fail 'reviewed physical foundation marker absent'
[[ $(< /sys/class/dmi/id/sys_vendor) == LENOVO ]] || fail 'wrong system vendor'
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail 'wrong product identity'
[[ $(< /sys/class/dmi/id/board_name) == LNVNB161216 ]] || fail 'wrong board identity'
[[ $(findmnt -n -o FSTYPE "$STATE") == btrfs ]] || fail 'APX state is not Btrfs'
[[ -f $RUNTIME_SOURCE && -f $CLIENT_SOURCE && -f $EXECUTOR_SOURCE ]] \
  || fail 'runtime source set is incomplete'
}

release_complete() {
  local role=$1
  local release=$2
  local root="$release/root"
  [[ -d $root && -f $release/manifest.json ]] || return 1
  python - "$release/manifest.json" "$role" <<'PY' || return 1
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    manifest = json.load(stream)
if (
    manifest.get("backend") != "systemd-nspawn-headless-physical-pilot-v1"
    or manifest.get("role") != sys.argv[2]
    or manifest.get("schema") != 1
):
    raise SystemExit(1)
PY
  local property
  property=$(btrfs property get -ts "$root" ro) || return 1
  [[ $property == *'ro=true'* ]]
}

assert_release_absent_or_complete() {
  local role=$1
  local release=$2
  [[ ! -e $release ]] && return 0
  release_complete "$role" "$release" && return 0
  fail "${release#$STATE/releases/} exists but is incomplete; preserve completed releases and run the documented targeted recovery if this is the known interrupted Development release"
}

recover_incomplete_development_release() {
  assert_release_absent_or_complete hub "$STATE/releases/hub-headless-v1"
  assert_release_absent_or_complete minimal "$STATE/releases/minimal-headless-v1"
  [[ -d $INCOMPLETE_DEVELOPMENT_RELEASE ]] \
    || fail 'known incomplete development-headless-v1 release is absent'
  if release_complete development "$INCOMPLETE_DEVELOPMENT_RELEASE"; then
    fail 'development-headless-v1 is complete and must not be deleted'
  fi
  [[ ! -e $INCOMPLETE_DEVELOPMENT_RELEASE/manifest.json ]] \
    || fail 'development-headless-v1 has a manifest and is not the known no-manifest partial state'
  printf 'Targeted destructive recovery:\n'
  printf '  path: %s\n' "$INCOMPLETE_DEVELOPMENT_RELEASE"
  printf '  reason: interrupted release creation left no manifest, so normal bootstrap must not skip it\n'
  printf '  preserved: completed Hub release and any other complete release\n'
  read -r -p "Type ${RECOVERY_APPROVAL}: " entered_approval
  [[ $entered_approval == "$RECOVERY_APPROVAL" ]] \
    || fail 'exact recovery approval was not entered'
  if [[ -d $INCOMPLETE_DEVELOPMENT_RELEASE/root ]]; then
    btrfs subvolume delete -R "$INCOMPLETE_DEVELOPMENT_RELEASE/root"
  fi
  rmdir "$INCOMPLETE_DEVELOPMENT_RELEASE"
  printf 'APX_INCOMPLETE_DEVELOPMENT_RELEASE_REMOVED\n'
}

verify_physical_target

case "${1:-}" in
  '')
    ;;
  --recover-incomplete-development-release)
    recover_incomplete_development_release
    exit 0
    ;;
  *)
    fail 'unknown bootstrap argument'
    ;;
esac

install -Dm0755 "$RUNTIME_SOURCE" /usr/lib/apx/apx-lab-runtime.py
install -Dm0755 "$CLIENT_SOURCE" /usr/lib/apx/apx-lab-client.py
install -Dm0755 "$EXECUTOR_SOURCE" /usr/lib/apx/apx-lab-executor.py
ln -sfn /usr/lib/apx/apx-lab-runtime.py /usr/bin/apx
mkdir -p "$STATE"/{releases,environments,plans,journal,snapshots,archives,quarantine,catalogue}
chmod 0700 "$STATE"/{releases,environments,plans,journal,snapshots,archives,quarantine,catalogue}
if btrfs quota status "$STATE" | grep -q 'Enabled:.*no'; then
  btrfs quota enable "$STATE"
  btrfs quota rescan -w "$STATE"
fi

remove_arch_install_scripts=no
if ! command -v pacstrap >/dev/null; then
  pacman -S --needed --noconfirm arch-install-scripts
  remove_arch_install_scripts=yes
fi

create_release() {
  local role=$1
  local release="$STATE/releases/${role}-headless-v1"
  local root="$release/root"
  if [[ -e $release ]]; then
    if release_complete "$role" "$release"; then
      return 0
    fi
    fail "${role}-headless-v1 exists but is incomplete; do not skip or overwrite it without the documented targeted recovery"
  fi
  mkdir -p "$release"
  btrfs subvolume create "$root"
  pacstrap -c "$root" base systemd python
  printf 'LANG=en_US.UTF-8\n' > "$root/etc/locale.conf"
  printf 'apx-%s-release\n' "$role" > "$root/etc/hostname"
  : > "$root/etc/machine-id"
  ln -sfn /run/systemd/resolve/stub-resolv.conf "$root/etc/resolv.conf"
  mkdir -p "$root/etc/systemd/network"
  cat > "$root/etc/systemd/network/20-host0.network" <<'EOF'
[Match]
Name=host0

[Network]
DHCP=yes
EOF
  systemd-nspawn -q -D "$root" systemctl enable \
    systemd-networkd.service systemd-resolved.service
  systemd-nspawn -q -D "$root" systemctl set-default multi-user.target
  systemd-nspawn -q -D "$root" useradd --create-home --uid 1000 \
    --user-group --shell /bin/bash apx
  passwd -R "$root" -l root

  case "$role" in
    hub)
      install -Dm0755 /usr/lib/apx/apx-lab-runtime.py "$root/usr/bin/apx"
      ;;
    development)
      systemd-nspawn -q --resolv-conf=replace-uplink -D "$root" \
        pacman -Syu --noconfirm --needed git base-devel nodejs npm
      ;;
    minimal) ;;
  esac

  rm -f "$root/etc/machine-id"
  : > "$root/etc/machine-id"
  rm -f "$root/var/lib/systemd/random-seed"
  cat > "$release/manifest.json" <<EOF
{"backend":"systemd-nspawn-headless-physical-pilot-v1","role":"${role}","schema":1,"source":"fresh-pacstrap-not-live-hub"}
EOF
  chmod 0400 "$release/manifest.json"
  btrfs property set -ts "$root" ro true
}

create_release hub
create_release development
create_release minimal

if [[ -e $STATE/releases/hub-headless-v3 ]]; then
  release_complete hub "$STATE/releases/hub-headless-v3" \
    || fail 'hub-headless-v3 exists but is incomplete; preserve it for manual inspection'
else
  mkdir -p "$STATE/releases/hub-headless-v3"
  btrfs subvolume snapshot \
    "$STATE/releases/hub-headless-v1/root" \
    "$STATE/releases/hub-headless-v3/root"
  install -Dm0755 /usr/lib/apx/apx-lab-client.py \
    "$STATE/releases/hub-headless-v3/root/usr/bin/apx"
  cat > "$STATE/releases/hub-headless-v3/manifest.json" <<'EOF'
{"backend":"systemd-nspawn-headless-physical-pilot-v1","client":"typed-unix-v1","role":"hub","schema":1,"source":"hub-headless-v1-plus-unprivileged-client"}
EOF
  chmod 0400 "$STATE/releases/hub-headless-v3/manifest.json"
  btrfs property set -ts "$STATE/releases/hub-headless-v3/root" ro true
fi

cat > /etc/systemd/system/apx-pilot-executor.service <<'EOF'
[Unit]
Description=APX physical pilot typed executor
After=local-fs.target systemd-machined.service
RequiresMountsFor=/var/lib/apx

[Service]
Type=simple
ExecStart=/usr/lib/apx/apx-lab-executor.py
Restart=on-failure
RestartSec=1s
NoNewPrivileges=no

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now apx-pilot-executor.service

if [[ $remove_arch_install_scripts == yes ]]; then
  pacman -Rns --noconfirm arch-install-scripts
fi

printf 'APX_PHYSICAL_HEADLESS_BOOTSTRAP_COMPLETE\n'
apx status
