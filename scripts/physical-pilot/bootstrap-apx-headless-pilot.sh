#!/usr/bin/env bash

set -euo pipefail
export LC_ALL=C

readonly SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly REPOSITORY=$(cd -- "$SCRIPT_DIR/../.." && pwd)
readonly STATE=/var/lib/apx
readonly RUNTIME_SOURCE=$REPOSITORY/scripts/virtual-lab/apx-lab-runtime.py
readonly CLIENT_SOURCE=$REPOSITORY/scripts/virtual-lab/apx-lab-client.py
readonly EXECUTOR_SOURCE=$REPOSITORY/scripts/virtual-lab/apx-lab-executor.py
readonly ENVIRONMENT_FEATURES_SOURCE=$REPOSITORY/src/apx_environment_features.py

fail() {
  printf 'APX physical bootstrap refused: %s\n' "$*" >&2
  exit 1
}

quota_state() {
  python -c '
import sys

fields = {}
for raw_line in sys.stdin:
    if ":" not in raw_line:
        continue
    key, value = raw_line.split(":", 1)
    key = " ".join(key.strip().lower().split())
    value = " ".join(value.strip().lower().split())
    if key in {"enabled", "status", "mode", "inconsistent", "override limits", "rescan status"}:
        if key in fields:
            raise SystemExit(1)
        fields[key] = value

enabled_values = [fields[key] for key in ("enabled", "status") if key in fields]
if len(enabled_values) != 1:
    raise SystemExit(1)
enabled = enabled_values[0]
if enabled in {"no", "disabled"}:
    print("disabled")
elif (
    enabled in {"yes", "enabled"}
    and fields.get("mode") in {"qgroup", "qgroup (full accounting)"}
    and fields.get("inconsistent") == "no"
    and fields.get("override limits") != "yes"
    and fields.get("rescan status") != "running"
):
    print("healthy")
else:
    raise SystemExit(1)
'
}

[[ $(id -u) == 0 ]] || fail 'host root is required'
[[ $(systemd-detect-virt) == none ]] || fail 'physical-machine pilot required'
[[ $(< /etc/hostname) == apx-host ]] || fail 'wrong host identity'
[[ -f /etc/apx-physical-pilot ]] || fail 'reviewed physical foundation marker absent'
[[ $(< /sys/class/dmi/id/sys_vendor) == LENOVO ]] || fail 'wrong system vendor'
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail 'wrong product identity'
[[ $(< /sys/class/dmi/id/board_name) == LNVNB161216 ]] || fail 'wrong board identity'
[[ $(findmnt -n -o FSTYPE "$STATE") == btrfs ]] || fail 'APX state is not Btrfs'
[[ -f $RUNTIME_SOURCE && -f $CLIENT_SOURCE && -f $EXECUTOR_SOURCE && -f $ENVIRONMENT_FEATURES_SOURCE ]] \
  || fail 'runtime source set is incomplete'

install -Dm0755 "$RUNTIME_SOURCE" /usr/lib/apx/apx-lab-runtime.py
install -Dm0755 "$CLIENT_SOURCE" /usr/lib/apx/apx-lab-client.py
install -Dm0755 "$EXECUTOR_SOURCE" /usr/lib/apx/apx-lab-executor.py
install -Dm0644 "$ENVIRONMENT_FEATURES_SOURCE" /usr/lib/apx/apx_environment_features.py
ln -sfn /usr/lib/apx/apx-lab-runtime.py /usr/bin/apx
mkdir -p "$STATE"/{releases,environments,plans,journal,snapshots,archives,quarantine,catalogue}
chmod 0700 "$STATE"/{releases,environments,plans,journal,snapshots,archives,quarantine,catalogue}
quota_status=$(btrfs quota status "$STATE") \
  || fail 'Btrfs quota status is unavailable'
state=$(quota_state <<<"$quota_status") \
  || fail 'Btrfs quota status is malformed, unsupported, or unhealthy'
if [[ $state == disabled ]]; then
  btrfs quota enable "$STATE"
  btrfs quota rescan -w "$STATE"
  quota_status=$(btrfs quota status "$STATE") \
    || fail 'Btrfs quota status is unavailable after enablement'
  [[ $(quota_state <<<"$quota_status") == healthy ]] \
    || fail 'Btrfs quota accounting is not healthy after enablement'
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
  [[ ! -e $release ]] || return 0
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
      systemd-nspawn -q --resolv-conf=copy-host -D "$root" \
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

if [[ ! -e $STATE/releases/hub-headless-v3 ]]; then
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

install -Dm0644 "$REPOSITORY/config/systemd/apx-pilot-executor.service" \
  /etc/systemd/system/apx-pilot-executor.service
systemctl daemon-reload
systemctl enable --now apx-pilot-executor.service

if [[ $remove_arch_install_scripts == yes ]]; then
  pacman -Rns --noconfirm arch-install-scripts
fi

printf 'APX_PHYSICAL_HEADLESS_BOOTSTRAP_COMPLETE\n'
apx status
