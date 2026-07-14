#!/usr/bin/env bash

set -euo pipefail
export LC_ALL=C

readonly STATE=/var/lib/apx
readonly SOURCE=/root/apx-lab-runtime.py
readonly CLIENT_SOURCE=/root/apx-lab-client.py
readonly EXECUTOR_SOURCE=/root/apx-lab-executor.py

[[ $(id -u) == 0 ]] || { echo 'APX bootstrap refused: host root required' >&2; exit 1; }
[[ $(systemd-detect-virt) == kvm ]] || { echo 'APX bootstrap refused: not the reviewed KVM guest' >&2; exit 1; }
[[ $(< /etc/hostname) == apx-virtual ]] || { echo 'APX bootstrap refused: wrong guest' >&2; exit 1; }
[[ -f $SOURCE ]] || { echo 'APX bootstrap refused: runtime source absent' >&2; exit 1; }
[[ -f $CLIENT_SOURCE ]] || { echo 'APX bootstrap refused: Hub client source absent' >&2; exit 1; }
[[ -f $EXECUTOR_SOURCE ]] || { echo 'APX bootstrap refused: executor source absent' >&2; exit 1; }
[[ $(findmnt -n -o FSTYPE "$STATE") == btrfs ]] || { echo 'APX bootstrap refused: state is not Btrfs' >&2; exit 1; }

install -Dm0755 "$SOURCE" /usr/lib/apx/apx-lab-runtime.py
install -Dm0755 "$CLIENT_SOURCE" /usr/lib/apx/apx-lab-client.py
install -Dm0755 "$EXECUTOR_SOURCE" /usr/lib/apx/apx-lab-executor.py
ln -sfn /usr/lib/apx/apx-lab-runtime.py /usr/bin/apx
mkdir -p "$STATE"/{releases,environments,plans,journal,snapshots,archives,quarantine,catalogue}
chmod 0700 "$STATE"/{releases,environments,plans,journal,snapshots,archives,quarantine,catalogue}
if btrfs quota status "$STATE" | grep -q 'Enabled:.*no'; then
  btrfs quota enable "$STATE"
  btrfs quota rescan -w "$STATE"
fi

if ! command -v pacstrap >/dev/null; then
  pacman -S --needed --noconfirm arch-install-scripts
fi

create_release() {
  local role=$1
  local release="$STATE/releases/${role}-headless-v1"
  local root="$release/root"
  [[ ! -e $release ]] || return 0
  mkdir -p "$release"
  btrfs subvolume create "$root"
  # The already verified VM host keyring is copied into the new release. Each
  # release still receives its own package database and writable package root.
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
  systemd-nspawn -q -D "$root" systemctl enable systemd-networkd.service systemd-resolved.service
  systemd-nspawn -q -D "$root" systemctl set-default multi-user.target
  systemd-nspawn -q -D "$root" useradd --create-home --uid 1000 --user-group --shell /bin/bash apx
  passwd -R "$root" -l root

  case "$role" in
    hub)
      install -Dm0755 /usr/lib/apx/apx-lab-runtime.py "$root/usr/bin/apx"
      ;;
    development)
      rm -f "$root/etc/resolv.conf"
      printf 'nameserver 10.0.2.3\n' > "$root/etc/resolv.conf"
      systemd-nspawn -q --resolv-conf=off -D "$root" \
        pacman -Syu --noconfirm --needed git base-devel nodejs npm
      ln -sfn /run/systemd/resolve/stub-resolv.conf "$root/etc/resolv.conf"
      ;;
    minimal) ;;
  esac

  rm -f "$root/etc/machine-id"
  : > "$root/etc/machine-id"
  rm -f "$root/var/lib/systemd/random-seed"
  cat > "$release/manifest.json" <<EOF
{"backend":"systemd-nspawn-headless-v1","role":"${role}","schema":1,"source":"fresh-pacstrap-not-live-hub"}
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
{"backend":"systemd-nspawn-headless-v1","client":"typed-unix-v1","role":"hub","schema":1,"source":"hub-headless-v1-plus-unprivileged-client"}
EOF
  chmod 0400 "$STATE/releases/hub-headless-v3/manifest.json"
  btrfs property set -ts "$STATE/releases/hub-headless-v3/root" ro true
fi

cat > /etc/systemd/system/apx-lab-executor.service <<'EOF'
[Unit]
Description=APX disposable typed executor
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
systemctl enable --now apx-lab-executor.service

pacman -Rns --noconfirm arch-install-scripts
rm -f "$SOURCE" "$CLIENT_SOURCE" "$EXECUTOR_SOURCE"
printf 'APX_HEADLESS_RUNTIME_BOOTSTRAP_COMPLETE\n'
