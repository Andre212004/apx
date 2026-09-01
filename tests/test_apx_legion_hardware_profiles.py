from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LegionHardwareProfileSourceTests(unittest.TestCase):
    def test_kernel_bridge_is_exact_model_and_closed_wmi_surface(self):
        source = (ROOT / "scripts/physical-pilot/kernel/apx-legion-gpu-profile-v1.c").read_text()
        for required in (
            'dmi_match(DMI_PRODUCT_NAME, "82JU")',
            'APX_GAMEZONE_GUID "887B54E3-DDDC-4B2C-8B88-68A26A8835D0"',
            "APX_WMI_IS_SUPPORT_HYBRID 40", "APX_WMI_SET_HYBRID 42",
            "APX_WMI_IS_SUPPORT_IGPU 63", "APX_WMI_SET_IGPU 65",
            "apx_legion_gpu_profile_v1", "MODULE_LICENSE(\"GPL\")",
        ):
            self.assertIn(required, source)
        self.assertNotIn("debugfs", source)
        self.assertNotIn("ec_write", source)

    def test_hub_menu_exposes_only_firmware_gpu_profiles(self):
        source = (ROOT / ".apx-live-shell-bluetooth-v1.qml").read_text()
        for required in (
            "SILENCIOSO", "NORMAL", "PERFORMANCE",
            "[ HÍBRIDO ] AMD + NVIDIA sob pedido",
            "[ NVIDIA ] dedicada", "REINICIAR AGORA", "MAIS TARDE",
            "gpu-prepare", "gpu-confirm", "Brilho do ecrã",
            "display-set", "displayBrightnessDebounce",
            "cycleKeyboardBrightness", 'text: "TECLADO"', "keyboard-cycle",
            "apx-legion-brightness-keys-v1.py",
            "function volumeMute(): void", "function microphoneMute(): void",
            "microphoneProcess", "@DEFAULT_AUDIO_SOURCE@",
        ):
            self.assertIn(required, source)
        self.assertNotIn("[ AMD ] apenas integrada", source)
        self.assertNotIn("AMD apenas é uma política APX", source)
        self.assertNotIn("LUZ OFF", source)
        self.assertNotIn("LUZ MÉD", source)
        self.assertNotIn("LUZ MAX", source)
        self.assertNotIn("keyboardBrightnessSummaryButton", source)
        self.assertNotIn("enabled: !displayBrightnessProcess.running", source)

    def test_brightness_key_bridge_is_exact_and_does_not_use_uinput(self):
        source = (ROOT / "scripts/physical-pilot/apx-legion-brightness-keys-v1.py").read_text()
        for required in (
            "ITE Tech. Inc. ITE Device(8910) Keyboard",
            "AT Translated Set 2 keyboard",
            "apx-legion-brightness-keys-v1.lock", "fcntl.LOCK_EX | fcntl.LOCK_NB",
            "KEY_PRINT = 99",
            "KEY_BRIGHTNESSDOWN = 224", "KEY_BRIGHTNESSUP = 225",
            'name == ITE_NAME and code == KEY_BRIGHTNESSDOWN',
            'name == ITE_NAME and code == KEY_BRIGHTNESSUP',
            'call_shell("brightnessDown")', 'call_shell("brightnessUp")',
            'name == AT_NAME and code == KEY_PRINT',
        ):
            self.assertIn(required, source)
        for raw_key in ("KEY_F1", "KEY_F2", "KEY_F3", "KEY_F4", "KEY_F5", "KEY_F6",
                        "KEY_F7", "KEY_F8", "KEY_F9", "KEY_F10", "KEY_F11", "KEY_F12"):
            self.assertNotIn(raw_key, source)
        self.assertNotIn("/dev/uinput", source)
        self.assertNotIn("EVIOCGRAB", source)
        self.assertNotIn("elif code == KEY_BRIGHTNESS", source)

    def test_hotkey_osd_covers_brightness_audio_radio_and_laptop_actions(self):
        source = (ROOT / "config/environment-shell-v1/quickshell/apx/shell.qml").read_text()
        for required in (
            "id: hotkeyOsdWindow", "property real hotkeyOsdOpacity", "showHotkeyOsd(",
            '"Brilho do ecrã"', '"Modo de avião"', '"Volume"', '"Microfone"',
            "hotkeyTouchpadOn", "hotkeyDisplayExtended", "hotkeyCalculatorMissing",
            "hotkeyScreenshot", "hotkeyScreenshotUnavailable", "hotkeyOverview",
            "hotkeyAirplaneOn", "hotkeyAirplaneOff", "hotkeyTouchpadToggled",
            "id: radioStatusProcess",
            'for directory in /sys/class/rfkill/rfkill*',
            'printf \'{\\"airplane_mode\\":%s}\\\\n\'',
        ):
            self.assertIn(required, source)
        self.assertIn('color: "#dc10181e"', source)

    def test_module_rebuild_and_recovery_are_documented(self):
        hook = (ROOT / "config/pacman-hooks/95-apx-legion-gpu-profile-v1.hook").read_text()
        build = (ROOT / "scripts/physical-pilot/apx-legion-gpu-profile-build-v1.sh").read_text()
        document = (ROOT / "docs/legion-hardware-profiles-v1-2026-08-04.md").read_text()
        self.assertIn("Target = linux-headers", hook)
        self.assertIn("scripts/sign-file", build)
        self.assertIn("tty1 remains the recovery boundary", document)
        self.assertIn("iGPU-only support value `0`", document)


if __name__ == "__main__":
    unittest.main()
