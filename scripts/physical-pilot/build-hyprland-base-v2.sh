#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C

readonly STATE=/var/lib/apx
readonly SOURCE=$STATE/releases/hyprland-base-v1/root
readonly RELEASE=$STATE/releases/hyprland-base-v2
readonly ROOT=$RELEASE/root
readonly ASSETS=/root/apx-host-development-mode-v1/apx/config/hyprland-base
readonly PROFILE=apx-hyprland-base-v2

fail() {
  printf 'APX graphical base v2 refused: %s\n' "$*" >&2
  exit 1
}

[[ $(id -u) == 0 ]] || fail 'Host root is required'
[[ $(< /etc/hostname) == apx-host ]] || fail 'wrong Host identity'
[[ -f /etc/apx-physical-pilot ]] || fail 'physical-pilot marker is absent'
[[ -d $SOURCE && ! -L $SOURCE ]] || fail 'admitted v1 source release is absent'
[[ $(btrfs property get -ts "$SOURCE") == 'ro=true' ]] || fail 'v1 source release is mutable'
[[ ! -e $RELEASE ]] || fail 'v2 release or staging state already exists'
[[ -d $ASSETS && ! -L $ASSETS ]] || fail 'reviewed graphical assets are absent'

install -d -m0700 "$RELEASE"
btrfs subvolume snapshot "$SOURCE" "$ROOT"
btrfs property set -ts "$ROOT" ro false
install -Dm0644 /etc/pacman.d/mirrorlist "$ROOT/etc/pacman.d/mirrorlist"
install -d -m0700 "$ROOT/etc/pacman.d/gnupg"
# Releases must carry their own writable package-signing trust database.  A
# read-only bind from the Host lets signature checks pass during the build but
# prevents archlinux-keyring's post-transaction hook from updating the image.
cp -a /etc/pacman.d/gnupg/. "$ROOT/etc/pacman.d/gnupg/"
sed -i '/^#\[multilib\]$/,/^#Include = \/etc\/pacman.d\/mirrorlist$/ s/^#//' \
  "$ROOT/etc/pacman.conf"

# The build is intentionally low-priority: creating a base must not make the
# interactive HUB feel frozen. A failed build remains writable and unpublished
# for explicit inspection; it is never admitted automatically.
/usr/bin/nice -n 15 /usr/bin/ionice -c 3 /usr/bin/systemd-nspawn -q \
  -D "$ROOT" \
  /usr/bin/pacman -Syu --needed --noconfirm \
  base base-devel bash-completion ca-certificates dbus-broker egl-gbm fastfetch \
  file-roller flatpak git gnome-keyring gvfs gvfs-gphoto2 gvfs-mtp gvfs-smb \
  hyprland hypridle hyprlock hyprpolkitagent kitty less libnotify mako man-db \
  lib32-mesa lib32-nvidia-utils lib32-vulkan-icd-loader lib32-vulkan-radeon \
  mousepad nano noto-fonts nvidia-utils pacman-contrib pipewire pipewire-pulse quickshell \
  ristretto rofi sudo thunar tumbler udiskie udisks2 vulkan-radeon vulkan-tools waybar \
  wireplumber xdg-desktop-portal xdg-desktop-portal-gtk \
  xdg-desktop-portal-hyprland xdg-user-dirs xdg-utils

/usr/bin/systemd-nspawn -q -D "$ROOT" /usr/bin/usermod -aG wheel apx
install -d -m0755 "$ROOT/etc/apx" "$ROOT/etc/sudoers.d"
printf '%s\n' '%wheel ALL=(ALL:ALL) ALL' 'apx ALL=(ALL:ALL) ALL' \
  | install -m0440 /dev/stdin "$ROOT/etc/sudoers.d/10-apx-local-admin"

sed -i 's/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' "$ROOT/etc/locale.gen"
sed -i 's/^#pt_PT.UTF-8 UTF-8/pt_PT.UTF-8 UTF-8/' "$ROOT/etc/locale.gen"
/usr/bin/systemd-nspawn -q -D "$ROOT" /usr/bin/locale-gen
printf 'LANG=en_US.UTF-8\n' > "$ROOT/etc/locale.conf"
printf 'apx-hyprland-base-v2\n' > "$ROOT/etc/hostname"
: > "$ROOT/etc/machine-id"

install -Dm0644 /dev/stdin "$ROOT/etc/systemd/network/20-host0.network" <<'EOF'
[Match]
Name=host0

[Network]
DHCP=yes
LinkLocalAddressing=ipv4
IPv6AcceptRA=no
DNS=1.1.1.1
DNS=9.9.9.9

[DHCPv4]
UseDNS=no
EOF
ln -sfn ../run/systemd/resolve/stub-resolv.conf "$ROOT/etc/resolv.conf"
/usr/bin/systemd-nspawn -q -D "$ROOT" /usr/bin/systemctl enable \
  systemd-networkd.service systemd-resolved.service paccache.timer
/usr/bin/systemd-nspawn -q -D "$ROOT" /usr/bin/flatpak remote-add --system \
  --if-not-exists flathub https://dl.flathub.org/repo/

readonly SEED=$ROOT/usr/share/apx/config-seeds/hyprland-minimal-v2
for relative in \
  alacritty/alacritty.toml fastfetch/apx-logo.txt fastfetch/config.jsonc \
  rofi/config.rasi waybar/config.json waybar/style.css; do
  install -Dm0644 "$ASSETS/$relative" "$SEED/$relative"
done
install -Dm0644 "$ASSETS/hyprland.conf" "$SEED/hyprland/hyprland.conf"

install -d -m0755 "$ROOT/var/lib/systemd/linger"
find "$ROOT/var/log" -xdev -type f -exec truncate -s0 -- {} +
/usr/bin/systemd-nspawn -q -D "$ROOT" /usr/bin/paccache -rk2 || true
/usr/bin/systemd-nspawn -q -D "$ROOT" /usr/bin/pacman-key --list-keys >/dev/null
[[ -s $ROOT/etc/pacman.d/gnupg/pubring.gpg ]] \
  || fail 'package-signing keyring is absent from the candidate release'

package_manifest=$(mktemp)
/usr/bin/systemd-nspawn -q -D "$ROOT" /usr/bin/pacman -Q \
  | /usr/bin/sort > "$package_manifest"
package_digest=$(sha256sum "$package_manifest" | awk '{print $1}')
package_count=$(wc -l < "$package_manifest")
install -Dm0444 "$package_manifest" "$RELEASE/packages.txt"
rm -f -- "$package_manifest"

python - "$RELEASE/manifest.json" "$package_digest" "$package_count" <<'PY'
import json
import os
from pathlib import Path
import sys

path = Path(sys.argv[1])
payload = {
    "config_seed": "hyprland-minimal-v2",
    "package_count": int(sys.argv[3]),
    "package_manifest_sha256": sys.argv[2],
    "profile": "apx-hyprland-base-v2",
    "release": "hyprland-base-v2",
    "package_signing_keyring": "embedded-and-readable",
    "normal_desktop_defaults": ["flathub", "networkd", "paccache", "resolved"],
    "schema": 2,
    "source": "immutable-hyprland-base-v1-plus-reviewed-package-and-config-update",
}
descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
try:
    os.write(descriptor, (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode())
    os.fsync(descriptor)
finally:
    os.close(descriptor)
PY

btrfs property set -ts "$ROOT" ro true
[[ $(btrfs property get -ts "$ROOT") == 'ro=true' ]] || fail 'v2 root was not sealed'
printf 'APX_HYPRLAND_BASE_V2_BUILT packages=%s manifest_sha256=%s\n' \
  "$package_count" "$package_digest"
