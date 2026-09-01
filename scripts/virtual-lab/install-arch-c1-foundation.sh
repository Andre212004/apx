#!/usr/bin/env bash

set -euo pipefail
export LC_ALL=C

readonly DISK=/dev/vda
readonly EXPECTED_BYTES=68719476736
readonly APPROVAL='ERASE-/dev/vda-DISPOSABLE-APX-C0-C6'
readonly LUKS_PASSPHRASE='apx-disposable-recovery-2026'
readonly ROOT_PASSWORD='apx-disposable-root-2026'
readonly SEED_ORIGIN='http://10.0.2.2:18080'
readonly CONTRACT_PACKAGE='apx-contracts-development-0.1.0.dev1-1-any.pkg.tar.zst'

fail() {
  printf 'APX virtual install refused: %s\n' "$*" >&2
  exit 1
}

[[ ${APX_DISPOSABLE_DISK_APPROVAL:-} == "$APPROVAL" ]] \
  || fail 'exact disposable-disk approval is absent'
virtualization=$(systemd-detect-virt)
[[ $virtualization == kvm || $virtualization == qemu ]] \
  || fail 'runtime is not QEMU/KVM'
[[ $(< /proc/sys/kernel/hostname) == archiso ]] \
  || fail 'runtime is not the reviewed Arch ISO'
[[ -b $DISK ]] || fail '/dev/vda is not a block device'
[[ $(blockdev --getsize64 "$DISK") == "$EXPECTED_BYTES" ]] \
  || fail '/dev/vda is not the fixed 64 GiB virtual disk'
[[ $(findmnt -rn -S "$DISK" | wc -l) == 0 ]] || fail '/dev/vda is mounted'
[[ $(cat /sys/class/dmi/id/product_name) == 'Standard PC (Q35 + ICH9, 2009)' ]] \
  || fail 'unexpected virtual machine identity'

timedatectl set-ntp true
until timedatectl show -p NTPSynchronized --value | grep -qx yes; do
  sleep 1
done

printf 'APX virtual install: destroying only %s (%s bytes)\n' \
  "$DISK" "$EXPECTED_BYTES"

sgdisk --zap-all "$DISK"
sgdisk --new=1:0:+1GiB --typecode=1:ef00 --change-name=1:APX_EFI "$DISK"
sgdisk --new=2:0:0 --typecode=2:8309 --change-name=2:APX_CRYPT "$DISK"
partprobe "$DISK"
udevadm settle

mkfs.fat -F 32 -n APX_EFI /dev/vda1
printf '%s' "$LUKS_PASSPHRASE" \
  | cryptsetup luksFormat --batch-mode --type luks2 --pbkdf argon2id /dev/vda2 -
printf '%s' "$LUKS_PASSPHRASE" | cryptsetup open /dev/vda2 cryptroot -
mkfs.btrfs --force --label APX_ROOT /dev/mapper/cryptroot

mount /dev/mapper/cryptroot /mnt
for subvolume in @ @home @var_log @var_cache_pacman @snapshots @apx; do
  btrfs subvolume create "/mnt/${subvolume}"
done
umount /mnt

mount -o noatime,compress=zstd:3,subvol=@ /dev/mapper/cryptroot /mnt
mkdir -p /mnt/{boot,home,var/log,var/cache/pacman/pkg,var/lib/apx,.snapshots}
mount -o noatime,compress=zstd:3,subvol=@home /dev/mapper/cryptroot /mnt/home
mount -o noatime,compress=zstd:3,subvol=@var_log /dev/mapper/cryptroot /mnt/var/log
mount -o noatime,compress=zstd:3,subvol=@var_cache_pacman \
  /dev/mapper/cryptroot /mnt/var/cache/pacman/pkg
mount -o noatime,compress=zstd:3,subvol=@snapshots \
  /dev/mapper/cryptroot /mnt/.snapshots
mount -o noatime,compress=zstd:3,subvol=@apx /dev/mapper/cryptroot /mnt/var/lib/apx
mount /dev/vda1 /mnt/boot

sed -i 's/^#ParallelDownloads.*/ParallelDownloads = 5/' /etc/pacman.conf
pacstrap -K /mnt \
  base linux linux-firmware amd-ucode btrfs-progs cryptsetup iwd python gnupg \
  systemd

genfstab -U /mnt > /mnt/etc/fstab
printf 'apx-virtual\n' > /mnt/etc/hostname
ln -sf /usr/share/zoneinfo/America/Sao_Paulo /mnt/etc/localtime
arch-chroot /mnt hwclock --systohc
sed -i 's/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /mnt/etc/locale.gen
sed -i 's/^#pt_PT.UTF-8 UTF-8/pt_PT.UTF-8 UTF-8/' /mnt/etc/locale.gen
arch-chroot /mnt locale-gen
printf 'LANG=en_US.UTF-8\n' > /mnt/etc/locale.conf
printf 'KEYMAP=us\n' > /mnt/etc/vconsole.conf

sed -i \
  's/^HOOKS=.*/HOOKS=(base systemd autodetect microcode modconf kms keyboard sd-vconsole block sd-encrypt filesystems fsck)/' \
  /mnt/etc/mkinitcpio.conf
arch-chroot /mnt mkinitcpio -P
arch-chroot /mnt bootctl install

luks_uuid=$(cryptsetup luksUUID /dev/vda2)
mkdir -p /mnt/boot/loader/entries
cat > /mnt/boot/loader/loader.conf <<'EOF'
default apx-virtual.conf
timeout 2
console-mode keep
editor no
EOF
cat > /mnt/boot/loader/entries/apx-virtual.conf <<EOF
title APX Virtual Headless
linux /vmlinuz-linux
initrd /amd-ucode.img
initrd /initramfs-linux.img
options rd.luks.name=${luks_uuid}=cryptroot root=/dev/mapper/cryptroot rootflags=subvol=@ rw console=ttyS0,115200n8
EOF

mkdir -p /mnt/etc/systemd/network
cat > /mnt/etc/systemd/network/20-wired.network <<'EOF'
[Match]
Name=en*

[Network]
DHCP=yes
IPv6AcceptRA=yes
EOF
ln -sf /run/systemd/resolve/stub-resolv.conf /mnt/etc/resolv.conf
arch-chroot /mnt systemctl enable \
  systemd-networkd.service systemd-resolved.service serial-getty@ttyS0.service

printf 'root:%s\n' "$ROOT_PASSWORD" | arch-chroot /mnt chpasswd
mkdir -p /mnt/var/lib/apx/{catalogue,environments,journal,quarantine,releases}
chmod 0700 /mnt/var/lib/apx/{catalogue,environments,journal,quarantine,releases}

curl --fail --silent --show-error \
  --output "/mnt/root/${CONTRACT_PACKAGE}" \
  "${SEED_ORIGIN}/${CONTRACT_PACKAGE}"
printf '%s  %s\n' \
  9d6e53007bc56e8a9105f4ff65c14097dbec13aa8b0b4c7ddb70912b01b012fd \
  "/mnt/root/${CONTRACT_PACKAGE}" | sha256sum --check --strict
arch-chroot /mnt pacman -U --noconfirm "/root/${CONTRACT_PACKAGE}"
rm "/mnt/root/${CONTRACT_PACKAGE}"

cat > /mnt/etc/apx-virtual-release <<EOF
profile=apx-clean-install-foundation-v1
source_revision=c6f61ff7259fa71039c087023018731c6f3a774d
iso_sha256=e86295dc0bdf9b85a5a9256810c553239689d2ae8e80eeec81b4e2e910d8a6c0
contracts_package_sha256=9d6e53007bc56e8a9105f4ff65c14097dbec13aa8b0b4c7ddb70912b01b012fd
virtual_disk_bytes=${EXPECTED_BYTES}
luks_uuid=${luks_uuid}
EOF
chmod 0644 /mnt/etc/apx-virtual-release

mkdir -p /mnt/var/log/apx
cat > /mnt/var/log/apx/c1-install-result <<EOF
status=installed-awaiting-reboot-proof
disk=${DISK}
disk_bytes=${EXPECTED_BYTES}
uefi_partition=/dev/vda1
encrypted_partition=/dev/vda2
root_mapping=/dev/mapper/cryptroot
EOF
chmod 0600 /mnt/var/log/apx/c1-install-result
sync

printf 'APX_C1_INSTALL_COMPLETE luks_uuid=%s\n' "$luks_uuid"
