#!/usr/bin/env bash

set -euo pipefail
export LC_ALL=C

readonly DISK=/dev/nvme0n1
readonly EXPECTED_BYTES=512110190592
readonly EXPECTED_MODEL='SAMSUNG MZVLB512HBJQ-000L2'
readonly EXPECTED_SERIAL='S4DYNX0R253702'
readonly APPROVAL='ERASE-/dev/nvme0n1-S4DYNX0R253702-APX-PHYSICAL-PILOT'

fail() {
  printf 'APX physical pilot refused: %s\n' "$*" >&2
  exit 1
}

[[ $(id -u) == 0 ]] || fail 'Arch ISO root is required'
[[ $(systemd-detect-virt) == none ]] || fail 'a physical machine is required'
[[ $(< /proc/sys/kernel/hostname) == archiso ]] || fail 'not running in Arch ISO'
[[ -d /sys/firmware/efi/efivars ]] || fail 'ISO was not booted in UEFI mode'
[[ -b $DISK ]] || fail 'fixed NVMe disk is absent'
[[ $(blockdev --getsize64 "$DISK") == "$EXPECTED_BYTES" ]] \
  || fail 'NVMe size does not match the reviewed target'
model=$(< /sys/block/nvme0n1/device/model)
serial=$(< /sys/block/nvme0n1/device/serial)
[[ ${model//[[:space:]]/} == ${EXPECTED_MODEL//[[:space:]]/} ]] \
  || fail 'NVMe model does not match the reviewed target'
[[ ${serial//[[:space:]]/} == "$EXPECTED_SERIAL" ]] \
  || fail 'NVMe serial does not match the reviewed target'
[[ -z $(lsblk -nrpo MOUNTPOINTS "$DISK" | tr -d '[:space:]') ]] \
  || fail 'target disk or one of its partitions is mounted'

printf 'Fixed destructive target:\n'
lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,LABEL,MODEL,SERIAL "$DISK"
printf '\nThis permanently destroys every partition and file on %s.\n' "$DISK"
read -r -p "Type ${APPROVAL}: " entered_approval
[[ $entered_approval == "$APPROVAL" ]] || fail 'exact approval was not entered'

ping -c 1 -W 5 archlinux.org >/dev/null \
  || fail 'network is not ready; use wired Ethernet or configure iwctl'
timedatectl set-ntp true

sgdisk --zap-all "$DISK"
sgdisk --new=1:0:+1GiB --typecode=1:ef00 --change-name=1:APX_EFI "$DISK"
sgdisk --new=2:0:0 --typecode=2:8309 --change-name=2:APX_CRYPT "$DISK"
partprobe "$DISK"
udevadm settle

mkfs.fat -F 32 -n APX_EFI /dev/nvme0n1p1
printf 'Create the new LUKS recovery passphrase now. Do not reuse a web password.\n'
cryptsetup luksFormat --type luks2 --pbkdf argon2id /dev/nvme0n1p2
cryptsetup open /dev/nvme0n1p2 cryptroot
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
mount -o noatime,compress=zstd:3,subvol=@apx \
  /dev/mapper/cryptroot /mnt/var/lib/apx
mount /dev/nvme0n1p1 /mnt/boot

pacstrap -K /mnt \
  base linux linux-firmware amd-ucode btrfs-progs cryptsetup iwd python gnupg \
  systemd git

genfstab -U /mnt > /mnt/etc/fstab
printf 'apx-host\n' > /mnt/etc/hostname
ln -sf /usr/share/zoneinfo/America/Sao_Paulo /mnt/etc/localtime
arch-chroot /mnt hwclock --systohc
sed -i 's/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /mnt/etc/locale.gen
arch-chroot /mnt locale-gen
printf 'LANG=en_US.UTF-8\n' > /mnt/etc/locale.conf
printf 'KEYMAP=us\n' > /mnt/etc/vconsole.conf

sed -i \
  's/^HOOKS=.*/HOOKS=(base systemd autodetect microcode modconf kms keyboard sd-vconsole block sd-encrypt filesystems fsck)/' \
  /mnt/etc/mkinitcpio.conf
arch-chroot /mnt mkinitcpio -P
arch-chroot -S /mnt bootctl install

luks_uuid=$(cryptsetup luksUUID /dev/nvme0n1p2)
mkdir -p /mnt/boot/loader/entries
cat > /mnt/boot/loader/loader.conf <<'EOF'
default apx-headless.conf
timeout 3
console-mode keep
editor no
EOF
cat > /mnt/boot/loader/entries/apx-headless.conf <<EOF
title APX Headless Physical Pilot
linux /vmlinuz-linux
initrd /amd-ucode.img
initrd /initramfs-linux.img
options rd.luks.name=${luks_uuid}=cryptroot root=/dev/mapper/cryptroot rootflags=subvol=@ rw
EOF

mkdir -p /mnt/etc/systemd/network
cat > /mnt/etc/systemd/network/20-wired.network <<'EOF'
[Match]
Name=en*

[Network]
DHCP=yes
IPv6AcceptRA=yes
EOF
cat > /mnt/etc/systemd/network/25-wireless.network <<'EOF'
[Match]
Name=wl*

[Network]
DHCP=yes
IPv6AcceptRA=yes
EOF
ln -sf /run/systemd/resolve/stub-resolv.conf /mnt/etc/resolv.conf
arch-chroot /mnt systemctl enable \
  systemd-networkd.service systemd-resolved.service iwd.service

printf 'Create the temporary host root password. It is not the LUKS passphrase.\n'
arch-chroot /mnt passwd root
mkdir -p /mnt/var/lib/apx/{catalogue,environments,journal,quarantine,releases}
chmod 0700 /mnt/var/lib/apx/{catalogue,environments,journal,quarantine,releases}

cat > /mnt/etc/apx-physical-pilot <<EOF
profile=apx-physical-headless-pilot-v1
disk=${DISK}
disk_bytes=${EXPECTED_BYTES}
disk_model=${EXPECTED_MODEL}
disk_serial=${EXPECTED_SERIAL}
luks_uuid=${luks_uuid}
EOF
chmod 0600 /mnt/etc/apx-physical-pilot
sync

printf '\nAPX_PHYSICAL_ARCH_FOUNDATION_COMPLETE luks_uuid=%s\n' "$luks_uuid"
printf 'Unmount with umount -R /mnt, close cryptroot, and reboot only after reviewing the output.\n'
