# APX Physical Headless Development Handoff v1

Status: target-bound, hands-on experimental pilot. This guide is written for
the owner's current Lenovo Legion 5 and reaches a headless Hub plus a separate
Development Environment. It is not a production APX installer.

## Outcome

The intended end state is:

```text
UEFI -> LUKS unlock -> minimal Arch host -> headless Hub -> Development
```

The host has no KDE, Hyprland, display manager, browser, IDE, compiler, Codex,
or permanent source checkout. Development has Git, build tools, Node.js, npm,
Codex, and the APX repository. The Hub has only the bounded `apx` management
client. Graphical work begins only after this headless state is reproduced.

## Fixed Target

Every destructive step must stop if these observations differ:

- system vendor: `LENOVO`;
- product: `82JU`, Legion 5 15ACH6H;
- board: `LNVNB161216`;
- CPU: AMD Ryzen 5 5600H;
- target: `/dev/nvme0n1`;
- target model: `SAMSUNG MZVLB512HBJQ-000L2`;
- target serial: `S4DYNX0R253702`;
- exact target size: 512,110,190,592 bytes;
- boot mode: x86_64 UEFI;
- expected graphics: AMD Cezanne integrated plus NVIDIA RTX 3060 Mobile;
- expected network: Realtek RTL8111/8168 Ethernet and RTL8852AE Wi-Fi.

The pilot deliberately destroys every existing partition on that NVMe. It
must never be adapted to a different disk merely because `/dev/nvme0n1` exists.

## Before Rebooting Into the Installer

1. Open a private/incognito browser window with no GitHub session and confirm
   that `https://github.com/Andre212004/apx` and branch
   `agent/physical-headless-handoff` are visible. At the time this guide was
   prepared, anonymous access returned `404`; the owner must intentionally make
   the repository public before erasing the machine. Do not continue while it
   remains private.
2. Open this guide from another computer or phone. Keep that device available
   for ChatGPT, GitHub, and the ArchWiki throughout installation.
3. Prepare one current official Arch ISO USB and retain it as recovery media.
4. Verify the downloaded ISO checksum and signature using the current Arch
   download instructions.
5. Connect power and preferably wired Ethernet.
6. In firmware, use UEFI mode. The ordinary Arch ISO does not support Secure
   Boot, so disable Secure Boot for this pilot.
7. Understand that the existing local checkout, SSH key, browser sessions, and
   Codex configuration will be erased. The public GitHub repository is the
   recovery copy. GitHub authentication will be enrolled again inside
   Development.

Authoritative references:

- `https://wiki.archlinux.org/title/Installation_guide`;
- `https://wiki.archlinux.org/title/dm-crypt/Encrypting_an_entire_system`;
- `https://wiki.archlinux.org/title/Systemd-boot`;
- `https://developers.openai.com/codex/codex-manual.md`.

## ChatGPT Handoff Prompt

Send the following prompt to ChatGPT on the second device:

```text
Guide me through the APX physical headless pilot at:
https://github.com/Andre212004/apx/blob/agent/physical-headless-handoff/docs/physical-headless-development-handoff-v1.md

Rules:
1. Read the complete guide and PROJECT_STATE.md first.
2. Give me only one bounded command block at a time.
3. Ask me to paste the complete output before continuing.
4. Never infer a disk identity. The only admitted disk is /dev/nvme0n1,
   model SAMSUNG MZVLB512HBJQ-000L2, serial S4DYNX0R253702,
   size 512110190592 bytes.
5. Stop on any mismatch, command failure, unexpected mounted filesystem,
   extra disk, uncertain state, missing network, or failed verification.
6. Never weaken or remove a guard in either physical-pilot script.
7. Never run scripts/virtual-lab/install-arch-c1-foundation.sh physically.
8. Do not install a desktop or display manager.
9. Keep Git, Codex, compilers, and the source checkout in Development only.
10. Explain every destructive command before asking me to run it.
```

## Phase 1 — Boot and Inspect the Arch ISO

Boot the official Arch installation medium, select the normal x86_64 entry, and
do not start partitioning manually.

Run and send the output to ChatGPT:

```bash
test -d /sys/firmware/efi/efivars && echo UEFI_OK
systemd-detect-virt
cat /sys/class/dmi/id/sys_vendor
cat /sys/class/dmi/id/product_name
cat /sys/class/dmi/id/board_name
lsblk -e7 -o NAME,PATH,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINTS,MODEL,SERIAL
blockdev --getsize64 /dev/nvme0n1
ip -brief link
```

Expected virtualization is `none`. All fixed target facts above must match.
Configure Wi-Fi with `iwctl` only if wired Ethernet is unavailable, then prove
connectivity with `ping -c 1 archlinux.org`.

## Phase 2 — Acquire and Verify the Target-Bound Installer

Download only the reviewed branch version:

```bash
curl --fail --location --output /root/install-apx-pilot.sh \
  https://raw.githubusercontent.com/Andre212004/apx/refs/heads/agent/physical-headless-handoff/scripts/physical-pilot/install-arch-headless-pilot.sh
sha256sum /root/install-apx-pilot.sh
```

The required SHA-256 is:

```text
247819678e7323f825a7dcb822281230f17391ec9e6d43c4c3392435dcee506f
```

Do not continue if it differs. Read the destructive sections before execution:

```bash
sed -n '1,260p' /root/install-apx-pilot.sh
```

## Phase 3 — Install the Minimal Physical Foundation

Execute the script only after ChatGPT confirms every observation:

```bash
bash /root/install-apx-pilot.sh
```

The script independently verifies physical execution, `archiso`, UEFI, disk
path, exact size, model, serial, and absence of mounted target filesystems. It
then requires this exact interactive approval:

```text
ERASE-/dev/nvme0n1-S4DYNX0R253702-APX-PHYSICAL-PILOT
```

It will separately ask for:

- a new LUKS recovery passphrase;
- a temporary host-root password.

Never paste either secret into ChatGPT. Successful completion prints
`APX_PHYSICAL_ARCH_FOUNDATION_COMPLETE`.

Review `/mnt/etc/fstab`, `/mnt/etc/apx-physical-pilot`, and
`/mnt/boot/loader/entries/apx-headless.conf`. Then shut down the installation
state cleanly:

```bash
sync
umount -R /mnt
cryptsetup close cryptroot
reboot
```

Remove the USB when firmware restarts.

## Phase 4 — First Headless Boot

1. Unlock LUKS using the new recovery passphrase.
2. Log in as `root` using the separate temporary host password.
3. Verify the host before installing APX:

```bash
hostnamectl --static
findmnt / /home /var/lib/apx /boot
lsblk -f
systemctl is-system-running
systemctl --failed --no-legend
ip -brief address
ping -c 1 github.com
cat /etc/apx-physical-pilot
```

The hostname must be `apx-host`; `/var/lib/apx` must be Btrfs; failed services
must be empty. If Wi-Fi is needed, use `iwctl` to connect and allow the enabled
`iwd` plus `systemd-networkd` services to obtain an address.

## Phase 5 — Temporary Source Staging and APX Bootstrap

Clone the public recovery copy into temporary host staging:

```bash
git clone --branch agent/physical-headless-handoff --single-branch \
  https://github.com/Andre212004/apx.git /root/apx-bootstrap
cd /root/apx-bootstrap
git status --short
git log -1 --oneline
sha256sum scripts/physical-pilot/bootstrap-apx-headless-pilot.sh
```

The bootstrap SHA-256 must be:

```text
9c4c957f5bcc66ea15899a24a9f1444892f0a512a1ebb166555a1d3c0a162a4d
```

Review it, then run:

```bash
bash scripts/physical-pilot/bootstrap-apx-headless-pilot.sh
```

It refuses any virtual machine, wrong hostname, missing installation marker,
wrong Lenovo identity, non-Btrfs APX state, or incomplete runtime source. It
installs the experimental typed executor, creates immutable Hub, Development,
and Minimal releases, and removes `arch-install-scripts` if it installed that
temporary package.

Successful completion prints `APX_PHYSICAL_HEADLESS_BOOTSTRAP_COMPLETE`.

## Phase 6 — Create and Verify the Hub

The first creation is performed from the host bootstrap console because no Hub
exists yet:

```bash
apx environment create-plan hub --role hub > /root/hub-create.json
python -c 'import json; print(json.load(open("/root/hub-create.json"))["digest"])'
```

Copy the printed digest into `PLAN`:

```bash
PLAN=PASTE_THE_64_CHARACTER_DIGEST
apx environment create --plan "$PLAN" --approve 'CREATE hub AS hub'
apx environment start hub
machinectl show apx-hub -p State -p Leader
cat /var/lib/apx/environments/hub/registration.json
machinectl shell root@apx-hub /bin/bash -lc 'apx status; apx environment list'
```

Required facts: Hub release `hub-headless-v3`, state `running`, healthy host,
and working `apx` inside the Hub.

## Phase 7 — Create Development Through the Hub

Run one bounded Hub command:

```bash
machinectl shell root@apx-hub /bin/bash -lc '
set -e
apx environment create-plan development --role development >/tmp/create.json
plan=$(python -c "import json; print(json.load(open(\"/tmp/create.json\"))[\"digest\"])")
apx environment create --plan "$plan" --approve "CREATE development AS development"
apx environment start development
apx environment list
'
```

Then confirm that Development cannot see the Hub executor:

```bash
machinectl shell root@apx-development /bin/bash -lc '
test ! -e /run/apx/executor.sock
command -v git gcc node npm
command -v apx >/dev/null; test $? -ne 0
'
```

## Phase 8 — Put GitHub and Codex Inside Development

Enter Development as root from the temporary host console:

```bash
apx environment shell development
```

Inside Development, install only Development-local tooling and create the
working checkout owned by the internal `apx` user:

```bash
pacman -Syu --noconfirm --needed github-cli
install -d -o apx -g apx /home/apx/work
su - apx -c 'git clone --branch agent/physical-headless-handoff --single-branch https://github.com/Andre212004/apx.git /home/apx/work/apx'
su - apx
curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/codex-install.sh
sed -n '1,240p' /tmp/codex-install.sh
sh /tmp/codex-install.sh
rm /tmp/codex-install.sh
cd /home/apx/work/apx
git status
gh auth login --git-protocol ssh
codex login --device-auth
codex login status
codex
```

The standalone Codex installer and `codex login --device-auth` are the current
official headless routes. Complete GitHub and Codex authentication
interactively. Codex authentication is stored under the `apx` user's Codex
state or credential store inside Development and must never be printed, pasted
into ChatGPT, committed, or copied into the Hub.

The first Codex instruction should be:

```text
Read AGENTS.md, PROJECT_STATE.md, and
docs/physical-headless-development-handoff-v1.md completely. We are now inside
the physical APX Development Environment. Diagnose current status first. Do not
change the host or Hub directly. Keep source changes here, validate them, push
them to GitHub, and use the documented promotion boundary for host updates.
```

## Phase 9 — Remove Temporary Host Development State

Do this only after all of these are proven:

- Development restarts with its home intact;
- its repository has the expected branch and remote;
- GitHub push authentication works;
- Codex starts inside Development;
- Hub still has no Git, compiler, Node.js, npm, Codex, or source checkout.

Exit Development, stop it through APX, and remove only the temporary host
checkout and Git package:

```bash
exit
apx environment stop development
rm -rf --one-file-system /root/apx-bootstrap
pacman -Rns --noconfirm git
apx environment start development
```

The `rm` target must be exactly `/root/apx-bootstrap`. Do not generalize it.

## Expected Pilot Limitations

- This uses the VM-proven runtime with broader host-root privilege than the
  future production executor.
- It has no PAM owner login, graphical broker, Hyprland, Secure Boot, signed APX
  package, production trust ceremony, or automatic Development-to-host
  promotion.
- Local root in Development is not claimed safe against kernel attacks.
- Until the graphical broker exists, the host root console remains a temporary
  bootstrap/recovery surface.
- Host updates require a reviewed manual staging step; Development must never
  mount or edit the live Hub or `/var/lib/apx` directly.

These limitations are acceptable only for this owner-controlled development
machine. They must not be described as a production release.
