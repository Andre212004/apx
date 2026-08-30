from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
ONLINE = ROOT / "scripts/physical-pilot/reserve-native-windows-120gib-v1.sh"
INITRD = ROOT / "scripts/physical-pilot/apx-native-windows-maintenance-initrd-v1.sh"
PROBE = ROOT / "scripts/physical-pilot/apx-native-windows-probe-initrd-v1.sh"
UNIT = ROOT / "config/systemd/initrd/apx-native-windows-reserve-v1.service"
PROBE_UNIT = ROOT / "config/systemd/initrd/apx-native-windows-probe-v1.service"
HOOK = ROOT / "config/initcpio/install/apx_native_windows_reserve"
CMDLINE = ROOT / "config/kernel/apx-native-windows-maintenance-v1.cmdline"
ENTRY = ROOT / "config/systemd-boot/apx-native-windows-maintenance-v1.conf"
FINALIZE = ROOT / "scripts/physical-pilot/finalize-native-windows-storage-v1.sh"
INTERNAL_INSTALLER = ROOT / "scripts/physical-pilot/prepare-native-windows-internal-installer-v1.sh"
BOOT_INTERNAL_INSTALLER = ROOT / "scripts/physical-pilot/boot-native-windows-internal-installer-v1.sh"
REPAIR_WINPE_MEDIA = ROOT / "scripts/physical-pilot/repair-native-windows-winpe-media-v1.sh"
REPAIR_WINPE_MEDIA_V2 = ROOT / "scripts/physical-pilot/repair-native-windows-winpe-media-v2.sh"
WINPESHL = ROOT / "config/system-images-v1/windows-internal-winpe/winpeshl.ini"
WINPE_MEDIA_SCRIPT = ROOT / "config/system-images-v1/windows-internal-winpe/apx-media.cmd"
WIFI_DRIVER_MANIFEST = ROOT / "config/system-images-v1/windows-82ju-wifi-driver-v1.json"
STAGE_WIFI_DRIVER = ROOT / "scripts/physical-pilot/stage-native-windows-wifi-driver-v1.sh"
BOOT_WINDOWS_OOBE = ROOT / "scripts/physical-pilot/boot-native-windows-oobe-v1.sh"
LIFECYCLE_INITRD = ROOT / "scripts/physical-pilot/apx-native-windows-lifecycle-initrd-v1.sh"
LIFECYCLE_HOOK = ROOT / "config/initcpio/install/apx_native_windows_lifecycle"
LIFECYCLE_UNIT = ROOT / "config/systemd/initrd/apx-native-windows-lifecycle-v1.service"
LIFECYCLE_BUILD = ROOT / "scripts/physical-pilot/build-native-windows-lifecycle-uki-v1.sh"
LIFECYCLE_RUNNER = ROOT / "scripts/physical-pilot/apx-native-windows-lifecycle-v1.py"
LIFECYCLE_FINALIZER = ROOT / "scripts/physical-pilot/apx-native-windows-lifecycle-finalize-v1.py"
LIFECYCLE_FINALIZER_UNIT = ROOT / "config/systemd/apx-native-windows-lifecycle-finalize-v1.service"
INSTALLER_V2 = ROOT / "scripts/physical-pilot/prepare-native-windows-installer-v2.sh"
CURRENT_WINPE_REPAIR_V3 = ROOT / "scripts/physical-pilot/repair-current-native-windows-winpe-findstr-v3.sh"
CURRENT_WINDOWS_RESUME_V3 = ROOT / "scripts/physical-pilot/resume-current-native-windows-install-v3.sh"
REFRESH_INSTALLER_V2 = ROOT / "scripts/physical-pilot/refresh-native-windows-installer-v2.sh"
DEPLOY_MENU_RECOVERY_V1 = ROOT / "scripts/physical-pilot/deploy-native-windows-menu-recovery-v1.sh"
WINDOWS_POLICY = ROOT / "config/native-environments/windows-policy-v1.json"


class NativeWindowsStorageV1Tests(unittest.TestCase):
    def test_scripts_parse_without_executing(self) -> None:
        subprocess.run(("/usr/bin/bash", "-n", str(ONLINE)), check=True)
        subprocess.run(("/usr/bin/sh", "-n", str(INITRD)), check=True)
        subprocess.run(("/usr/bin/sh", "-n", str(PROBE)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(HOOK)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(FINALIZE)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(INTERNAL_INSTALLER)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(BOOT_INTERNAL_INSTALLER)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(REPAIR_WINPE_MEDIA)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(REPAIR_WINPE_MEDIA_V2)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(STAGE_WIFI_DRIVER)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(BOOT_WINDOWS_OOBE)), check=True)
        subprocess.run(("/usr/bin/sh", "-n", str(LIFECYCLE_INITRD)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(LIFECYCLE_HOOK)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(LIFECYCLE_BUILD)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(INSTALLER_V2)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(CURRENT_WINPE_REPAIR_V3)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(CURRENT_WINDOWS_RESUME_V3)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(REFRESH_INSTALLER_V2)), check=True)
        subprocess.run(("/usr/bin/bash", "-n", str(DEPLOY_MENU_RECOVERY_V1)), check=True)

    def test_online_experiment_is_permanently_retired(self) -> None:
        source = ONLINE.read_text()
        refusal = source.index('fail "online method retired; use APX Windows Storage Maintenance"')
        first_identity_gate = source.index('[[ $(/usr/bin/id -u) == 0 ]]')
        self.assertLess(refusal, first_identity_gate)

    def test_initrd_executor_closes_mapping_before_gpt_write(self) -> None:
        source = INITRD.read_text()
        shrink = source.index("btrfs filesystem resize 1:382169251840")
        unmount_esp = source.index('umount "$esp" || fail unmount-esp-before-storage')
        unmount = source.index('/usr/bin/umount "$work"')
        close = source.index("systemctl stop systemd-cryptsetup@cryptroot.service")
        partition = source.index('sfdisk --wipe never -N 2 "$disk"')
        self.assertLess(unmount_esp, shrink)
        self.assertLess(shrink, unmount)
        self.assertLess(unmount, close)
        self.assertLess(close, partition)
        self.assertIn("size=746457088", source)
        self.assertIn("128849354240", source)
        self.assertIn('test "$(/usr/bin/cat /sys/class/power_supply/ADP0/online)" = 1', source)
        self.assertIn("S4DYNX0R253702", source)

    def test_initrd_unit_precedes_sysroot_mount_and_is_one_shot(self) -> None:
        source = UNIT.read_text()
        self.assertIn("ConditionKernelCommandLine=apx.native_windows_reserve=1", source)
        self.assertIn("Before=sysroot.mount initrd-root-fs.target", source)
        self.assertIn("After=dev-mapper-cryptroot.device", source)
        self.assertIn("Type=oneshot", source)
        self.assertIn("TimeoutStartSec=infinity", source)
        self.assertIn("Requires=apx-native-windows-probe-v1.service", source)
        self.assertIn("After=systemd-fsck@dev-mapper-cryptroot.service", source)

    def test_probe_runs_before_unlock_and_records_to_esp(self) -> None:
        unit = PROBE_UNIT.read_text()
        probe = PROBE.read_text()
        self.assertIn("Before=systemd-cryptsetup@cryptroot.service", unit)
        self.assertIn("Requires=dev-nvme0n1p1.device", unit)
        self.assertIn("windows-storage-probe-v1.status", probe)
        self.assertIn("stage=uki-loaded-before-unlock", probe)

    def test_build_hook_embeds_only_fixed_executor_and_unit(self) -> None:
        source = HOOK.read_text()
        for binary in ("blockdev", "btrfs", "cryptsetup", "mountpoint", "sfdisk", "systemctl"):
            self.assertIn(f"/usr/bin/{binary}", source)
        self.assertIn("add_module vfat", source)
        self.assertIn("initrd-root-fs.target.wants/apx-native-windows-reserve-v1.service", source)
        self.assertIn("initrd-root-fs.target.wants/apx-native-windows-probe-v1.service", source)
        self.assertNotIn("eval", source)

    def test_boot_entry_and_cmdline_are_explicit(self) -> None:
        self.assertEqual(
            ENTRY.read_text(),
            "title APX Windows Storage Maintenance\nefi /EFI/APX/apx-native-windows-maintenance-v1.efi\n",
        )
        cmdline = CMDLINE.read_text()
        self.assertIn("rd.luks.name=3ad5fc06-c4eb-4bb2-936b-f75eff3bc1c4=cryptroot", cmdline)
        self.assertIn("apx.native_windows_reserve=1", cmdline)
        self.assertNotIn("quiet", cmdline)
        self.assertIn("systemd.journald.forward_to_console=1", cmdline)

    def test_finalizer_requires_exact_offline_result(self) -> None:
        source = FINALIZE.read_text()
        self.assertIn("success:128849354240", source)
        self.assertIn("382186029056", source)
        self.assertIn("746424320", source)
        self.assertIn("251658895", source)
        self.assertIn('install -m 0400 -o root -g root', source)

    def test_internal_installer_uses_only_reserved_tail(self) -> None:
        source = INTERNAL_INSTALLER.read_text()
        self.assertIn("readonly installer_start=981340160", source)
        self.assertIn("readonly installer_size=18874368", source)
        self.assertIn('name="APX_WINSETUP"', source)
        self.assertIn("-n APXWINSETUP", source)
        self.assertIn("sfdisk --append --no-reread --no-tell-kernel", source)
        self.assertIn("wimlib-imagex split", source)
        self.assertIn(" 3800 --check", source)
        self.assertIn("--exclude='./sources/install.wim'", source)
        self.assertNotIn("bsdtar -xpf", source)
        self.assertIn("--no-same-owner --no-same-permissions", source)
        self.assertNotIn("grep -Fq 'Microsoft Windows Production", source)
        self.assertIn("install3.swm", source)
        self.assertIn('unlink "$maintenance_uki"', source)
        self.assertNotIn("/dev/sda", source)

    def test_internal_installer_boot_is_one_shot_and_fail_closed(self) -> None:
        source = BOOT_INTERNAL_INSTALLER.read_text()
        self.assertIn("$1 == --validate-only || $1 == --reboot", source)
        self.assertIn("no boot was armed", source)
        self.assertIn("readonly installer_partition=/dev/nvme0n1p3", source)
        self.assertIn("readonly installer_partuuid=309BEBB6-5C32-4E21-9C92-6D758E51389D", source)
        self.assertIn("readonly expected_boot_order=2001,0005,0000,2002,2003", source)
        self.assertIn("efibootmgr -n", source)
        self.assertIn("efibootmgr -N", source)
        self.assertIn("systemctl reboot", source)
        self.assertNotIn("efibootmgr -o", source)
        self.assertNotIn("bootctl set-default", source)
        self.assertNotIn("/dev/sda", source)

    def test_winpe_installs_only_after_exact_disk_and_partition_identity(self) -> None:
        shell = WINPESHL.read_text()
        command = WINPE_MEDIA_SCRIPT.read_text()
        repair = REPAIR_WINPE_MEDIA_V2.read_text()
        self.assertIn("%SYSTEMROOT%\\System32\\wpeinit.exe", shell)
        self.assertIn("apx-media.cmd", shell)
        self.assertIn("uniqueid disk", command)
        self.assertIn("AC9FC0BD-2162-43A9-AAE6-3F654FF6F275", command)
        for label in ("APX_EFI", "APXWINTARGET", "APXWINSETUP"):
            self.assertIn(label, command)
        self.assertIn("ca7d7ccb-63ed-4c53-861c-1742536059cc", command)
        self.assertIn("call :validate_contract", command)
        self.assertIn("format fs=ntfs quick label=APXWINTARGET", command)
        self.assertIn("call :file_selected_size", command)
        self.assertIn("call :file_has_key_exact", command)
        self.assertIn("call :choose_letter SETUP W", command)
        self.assertIn("call :choose_letter WINDOWS C", command)
        self.assertIn("call :choose_letter EFI S", command)
        self.assertIn("call :mount_named_volume", command)
        self.assertIn("mountvol.exe !APX_MOUNT_LETTER!: !APX_VOLUME_SELECTED!", command)
        self.assertIn("mountvol.exe !APX_MOUNT_LETTER!: /L", command)
        self.assertIn("X:\\Windows\\System32\\find.exe", command)
        self.assertNotIn("file_contains", command)
        self.assertIn('if /I "%~3"=="WINDOWS"', command)
        self.assertEqual(command.lower().count("echo assign letter="), 1)
        self.assertIn("target-contract-revalidation", command)
        self.assertIn("/ImageFile:%APX_MEDIA%\\sources\\install.swm", command)
        self.assertIn("/SWMFile:%APX_MEDIA%\\sources\\install*.swm", command)
        self.assertIn("/Index:6 /ApplyDir:%APX_TARGET%", command)
        self.assertIn("bcdboot.exe %APX_TARGET%\\Windows /s %APX_ESP% /f UEFI /v", command)
        self.assertIn("bcdedit.exe /store", command)
        self.assertIn("bcdedit.exe /sysstore %APX_ESP%", command)
        self.assertIn("displayorder {bootmgr} /addlast", command)
        self.assertIn("\\EFI\\Microsoft\\Boot\\bootmgfw.efi", command)
        self.assertIn("\\Windows\\system32\\winload.efi", command)
        self.assertIn("status=boot-prepared", command)
        self.assertIn("status=failed", command)
        self.assertNotIn("findstr", command.lower())
        self.assertNotIn("remove letter=", command.lower())
        self.assertNotIn("setup.exe", command.lower())
        for forbidden in ("clean", "delete partition", "format fs=fat"):
            self.assertNotIn(forbidden, command.lower())
        self.assertIn("--check --rebuild", repair)
        self.assertIn("boot.wim.apx-original", repair)
        self.assertIn("boot.wim.apx-new", repair)
        self.assertIn("Windows/System32/mountvol.exe", repair)
        self.assertNotIn("/dev/sda", repair)

    def test_wifi_driver_staging_is_hardware_bound_and_offline_only(self) -> None:
        import json

        manifest = json.loads(WIFI_DRIVER_MANIFEST.read_text())
        source = STAGE_WIFI_DRIVER.read_text()
        self.assertEqual(manifest["hardware_id"], r"PCI\VEN_10EC&DEV_8852&SUBSYS_485217AA")
        self.assertEqual(manifest["lenovo_doc_id"], "DS551503")
        self.assertEqual(
            manifest["package_sha256"],
            "1defff5645c18427c5f1af5af07a0ebae1dde25c70c3624869d485cef06f0c04",
        )
        self.assertIn("readonly windows_partition=/dev/nvme0n1p4", source)
        self.assertIn("readonly windows_partuuid=099C31D8-313A-4ABA-B0E0-2B59502C9674", source)
        self.assertIn("C:\\\\APX\\\\Drivers\\\\Realtek8852AE", source)
        self.assertIn("Microsoft Windows Hardware Compatibility Publisher", source)
        self.assertNotIn("pnputil", source.lower())
        self.assertNotIn("dism", source.lower())
        self.assertNotIn("/dev/sda", source)

    def test_oobe_boot_is_windows_only_once_and_linux_stays_default(self) -> None:
        source = BOOT_WINDOWS_OOBE.read_text()
        self.assertIn("readonly windows_partition=/dev/nvme0n1p4", source)
        self.assertIn("readonly windows_esp=/dev/nvme0n1p6", source)
        self.assertIn("readonly expected_order=0005,0006,0000,2001,2002,2003", source)
        self.assertIn("HD(6,GPT,${windows_esp_partuuid,,}", source)
        self.assertIn("efibootmgr -n", source)
        self.assertIn("efibootmgr -N", source)
        self.assertIn("bcd_size -ge 16384", source)
        self.assertIn("handoff-$index", source)
        self.assertIn("systemctl reboot", source)
        self.assertNotIn("efibootmgr -o", source)
        self.assertNotIn("bootctl set-default", source)
        self.assertNotIn("/dev/sda", source)

    def test_repeatable_policy_has_three_bounded_sizes_and_one_instance(self) -> None:
        import json

        policy = json.loads(WINDOWS_POLICY.read_text())
        self.assertEqual(policy["profile"], "apx-native-windows-policy-v1")
        self.assertEqual(policy["size_choices_gib"], [80, 120, 160])
        self.assertEqual(policy["default_size_gib"], 120)
        self.assertEqual(policy["minimum_apx_size_gib"], 256)
        self.assertEqual(policy["max_instances"], 1)
        self.assertEqual(policy["disk_serial"], "S4DYNX0R253702")

    def test_repeatable_offline_executor_has_closed_create_and_delete_paths(self) -> None:
        source = LIFECYCLE_INITRD.read_text()
        self.assertIn("apx.native_windows_action=", source)
        self.assertIn("apx.native_windows_size_gib=", source)
        self.assertIn("case \"$size_gib\" in 80|120|160)", source)
        self.assertIn("target_btrfs_bytes", source)
        self.assertIn('btrfs filesystem resize "1:$target_btrfs_bytes"', source)
        self.assertLess(source.index("shrink-btrfs"), source.index("shrink-gpt"))
        for number in (3, 4):
            self.assertIn(f'blkdiscard -f \"/dev/nvme0n1p$number\"', source)
        self.assertLess(source.index("discard-p$number"), source.index("delete-windows-gpt"))
        self.assertIn("full_p2_sectors=998115983", source)
        self.assertIn("windows-identity", source)
        self.assertIn("setup-identity", source)
        self.assertIn("099c31d8-313a-4aba-b0e0-2b59502c9674", source)
        self.assertIn("309bebb6-5c32-4e21-9c92-6d758e51389d", source)
        for number in (3, 4):
            self.assertIn(
                f"blkid -p -s PART_ENTRY_TYPE -o value /dev/nvme0n1p{number}",
                source,
            )
        self.assertNotIn("blkid -s PART_ENTRY_TYPE", source)
        self.assertIn("success:delete", source)
        self.assertNotIn("/dev/sda", source)
        self.assertNotIn("eval", source)

    def test_lifecycle_uki_embeds_authenticated_operation(self) -> None:
        hook = LIFECYCLE_HOOK.read_text()
        unit = LIFECYCLE_UNIT.read_text()
        build = LIFECYCLE_BUILD.read_text()
        for binary in ("blkdiscard", "blkid", "btrfs", "cryptsetup", "sfdisk"):
            self.assertIn(f"/usr/bin/{binary}", hook)
        self.assertIn("ConditionKernelCommandLine=apx.native_windows_lifecycle=1", unit)
        self.assertIn("Before=sysroot.mount initrd-root-fs.target", unit)
        self.assertIn("apx.native_windows_action=$action", build)
        self.assertIn("apx.native_windows_size_gib=$size_gib", build)
        self.assertIn("apx.native_windows_generation=$generation", build)
        self.assertIn("mkinitcpio --nopost", build)
        self.assertIn("native-windows-lifecycle-$generation-", build)
        self.assertIn("sbverify --list", build)
        self.assertIn("bootctl list", build)
        self.assertIn("/usr/share/apx/native-windows-lifecycle-v1", build)
        self.assertIn("/usr/share/apx/native-windows-lifecycle-v1", hook)
        self.assertNotIn("/root/apx-host-development-mode-v1/apx", build)
        self.assertNotIn("/root/apx-host-development-mode-v1/apx", hook)
        self.assertNotIn("apx-native-windows-probe-v1.service", hook)
        self.assertNotIn("Requires=apx-native-windows-probe-v1.service", unit)

    def test_lifecycle_runner_is_reboot_bound_and_preserves_global_reserve(self) -> None:
        source = LIFECYCLE_RUNNER.read_text()
        self.assertIn("size_choices_gib", source)
        self.assertIn("32 * 1024**3", source)
        self.assertIn('cwd=Path("/")', source)
        self.assertNotIn("/root/apx-host-development-mode-v1/apx", source)
        self.assertIn("str(error)[-300:]", source)
        self.assertIn("BUILD, arguments.action", source)
        self.assertIn('efibootmgr", "--create-only"', source)
        self.assertNotIn('efibootmgr", "--create"', source)
        self.assertIn('"--label", MAINTENANCE_LABEL', source)
        self.assertIn('efibootmgr", "-n"', source)
        self.assertIn("ENTRY_FILE.unlink()", source)
        self.assertIn("def maintenance_entries()", source)
        self.assertIn("def boot_order()", source)
        self.assertIn("if boot_order() != permanent_order", source)
        self.assertIn('systemctl", "--no-block", "reboot"', source)
        self.assertIn("windows-pending.json", source)
        self.assertIn("os.O_NOFOLLOW", source)
        self.assertNotIn("shell=True", source)

    def test_new_installer_carries_wifi_and_return_without_external_tools(self) -> None:
        source = INSTALLER_V2.read_text()
        self.assertIn("80 || $size_gib == 120 || $size_gib == 160", source)
        self.assertIn('name="APX_WINDOWS_TARGET"', source)
        self.assertIn('name="APX_WINSETUP"', source)
        self.assertIn("mkfs.ntfs -F -Q -L APXWINTARGET", source)
        self.assertIn("apx-expected.ini", source)
        self.assertIn("wimlib-imagex update", source)
        self.assertIn("required WinPE executable is absent", source)
        self.assertIn("mountvol.exe", source)
        self.assertIn("grep -Fiq findstr", source)
        self.assertIn("APX-ReturnToHub.ps1", source)
        self.assertIn("APX-ProvisionHardware.cmd", source)
        self.assertIn("netrtwlane6.inf", source)
        self.assertNotIn('efibootmgr -n "$setup_entry"', source)
        self.assertIn("ready without reboot", source)
        self.assertIn("/usr/share/apx/native-windows-lifecycle-v1", source)
        self.assertIn("windows-installer-prepared-v2.json", source)
        self.assertIn("Created partitions, if any, were retained for explicit recovery", source)
        self.assertNotIn("/root/apx-host-development-mode-v1/apx", source)
        self.assertNotIn("/dev/sda", source)

    def test_finalizer_returns_deleted_space_and_publishes_only_complete_windows(self) -> None:
        source = LIFECYCLE_FINALIZER.read_text()
        unit = LIFECYCLE_FINALIZER_UNIT.read_text()
        self.assertIn('blockdev", "--getsize64", "/dev/mapper/cryptroot"', source)
        self.assertNotIn('cryptsetup", "resize", "cryptroot"', source)
        self.assertIn('btrfs", "filesystem", "resize", "1:max", "/"', source)
        self.assertIn('pending["stage"] = "finalizing"', source)
        self.assertIn('pending["stage"] = "preparing-installer"', source)
        self.assertIn('TERMINAL_STAGES = {"failed", "recovery-required"}', source)
        self.assertNotIn('"/usr/bin/efibootmgr", "-n"', source)
        self.assertNotIn('"systemctl", "--no-block", "reboot"', source)
        self.assertIn("if not users.is_dir() or users.is_symlink():", source)
        self.assertIn("def installer_status", source)
        self.assertIn("o WinPE parou em segurança", source)
        self.assertIn("9625F250-9ACC-453A-AE63-0C863ADE440F", source)
        self.assertIn("cleanup_windows_efi", source)
        self.assertIn("INSTALLER_MARKER.unlink", source)
        self.assertNotIn("/root/apx-host-development-mode-v1/apx", source)
        self.assertIn("METADATA.unlink", source)
        self.assertIn("LEGACY_STORAGE.unlink", source)
        self.assertIn("windows_complete()", source)
        self.assertIn("EXPECTED_RETURN_HASHES", source)
        self.assertIn('"netrtwlane6.inf_*"', source)
        self.assertIn("pci\\\\ven_10ec&dev_8852&subsys_485217aa", source)
        self.assertIn('raw.decode("utf-16"', source)
        self.assertIn("REGRESSAR AO APX.cmd", source)
        self.assertIn('"state": "ready"', source)
        self.assertIn("set_linux_first(windows_entry)", source)
        self.assertIn("ConditionPathExists=/var/lib/apx/native-environments/windows-pending.json", unit)
        self.assertIn("RequiresMountsFor=/boot /var/lib/apx", unit)
        self.assertNotIn("Restart=", unit)
        self.assertIn("TimeoutStartSec=30min", unit)
        self.assertIn("StartLimitBurst=3", unit)

    def test_current_findstr_recovery_is_exact_non_rebooting_and_separate_from_resume(self) -> None:
        repair = CURRENT_WINPE_REPAIR_V3.read_text()
        resume = CURRENT_WINDOWS_RESUME_V3.read_text()
        for source in (repair, resume):
            self.assertIn("890c5a4c-3b84-41ea-af57-2fb0043243b5", source)
            self.assertIn("309bebb6-5c32-4e21-9c92-6d758e51389d", source.lower())
            self.assertIn("099c31d8-313a-4aba-b0e0-2b59502c9674", source.lower())
            self.assertNotIn("mkfs", source.lower())
            self.assertNotIn("delete partition", source.lower())
            self.assertNotIn("blkdiscard", source.lower())
        self.assertIn("--prepare", repair)
        self.assertIn("boot.wim.apx-original", repair)
        self.assertIn("wimlib-imagex verify", repair)
        self.assertIn("cmp \"$backup/gpt-before.sfdisk\" \"$backup/gpt-after.sfdisk\"", repair)
        self.assertNotIn("systemctl start apx-native-windows-lifecycle-finalize", repair)
        self.assertNotIn("systemctl reboot", repair)
        self.assertIn("--reboot", resume)
        self.assertIn("wimlib-imagex verify", resume)
        self.assertIn("systemctl start apx-native-windows-lifecycle-finalize-v1.service", resume)

    def test_menu_retry_refreshes_only_authenticated_winpe_media(self) -> None:
        source = REFRESH_INSTALLER_V2.read_text()
        self.assertIn('pending.get("stage") != "installing"', source)
        self.assertIn('windows_start_sector', source)
        self.assertIn('len(set(raw)) != 1', source)
        self.assertIn("wimlib-imagex update", source)
        self.assertIn("wimlib-imagex verify", source)
        self.assertIn("diskpart.exe Dism.exe fc.exe find.exe", source)
        self.assertIn('extract "$setup_mount/sources/install.swm" 6 Windows/System32/fc.exe', source)
        self.assertIn('--ref="$setup_mount/sources/install*.swm" --to-stdout', source)
        self.assertIn('add "%s" /Windows/System32/fc.exe', source)
        self.assertIn("f4d29fd93794e50a6740b9692da5dcad119d0f5a68a812357497c69ed6496ce3", source)
        self.assertIn("boot.wim.apx-new", source)
        self.assertIn("boot.wim.apx-original", source)
        self.assertIn('cmp "$backup/gpt-before.sfdisk" "$backup/gpt-after.sfdisk"', source)
        self.assertIn("install-status-v2.ini", source)
        self.assertNotIn("mkfs", source.lower())
        self.assertNotIn("blkdiscard", source.lower())
        self.assertNotIn("sfdisk --delete", source.lower())
        self.assertNotIn("systemctl reboot", source.lower())

    def test_installer_injects_authenticated_comparison_executable(self) -> None:
        source = INSTALLER_V2.read_text()
        self.assertIn('extract "$iso_mount/sources/install.wim" 6 Windows/System32/fc.exe', source)
        self.assertIn('add "%s" /Windows/System32/fc.exe', source)
        self.assertIn("diskpart.exe Dism.exe fc.exe find.exe", source)
        self.assertIn("f4d29fd93794e50a6740b9692da5dcad119d0f5a68a812357497c69ed6496ce3", source)

    def test_menu_recovery_rollout_does_not_resume_or_touch_windows_media(self) -> None:
        source = DEPLOY_MENU_RECOVERY_V1.read_text()
        self.assertIn("apx-native-windows-recovery-v1.py", source)
        self.assertIn("refresh-native-windows-installer-v2.sh", source)
        self.assertIn("native_recovery", (ROOT / "scripts/physical-pilot/apx-environment-switch-v1.py").read_text())
        self.assertIn("never mounts or writes a Windows volume", source)
        self.assertIn("systemctl stop apx-native-windows-lifecycle-finalize-v1.service", source)
        self.assertNotIn("systemctl start apx-native-windows-lifecycle-finalize", source)
        self.assertNotIn("systemctl reboot", source)
        self.assertNotIn("efibootmgr -n", source)
        self.assertNotIn("/dev/nvme0n1p3", source)
        self.assertNotIn("/dev/nvme0n1p4", source)


if __name__ == "__main__":
    unittest.main()
