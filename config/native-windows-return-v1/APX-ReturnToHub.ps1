$ErrorActionPreference = "Stop"

# Older APX releases disabled Explorer's WIN+E action and then tried to claim
# the same OS-reserved chord through the global-hotkey API. Restore the fallback:
# the low-level hook below suppresses WIN+E only while APX is actually running.
$advanced = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
$disabled = (Get-ItemProperty -Path $advanced -Name DisabledHotkeys -ErrorAction SilentlyContinue).DisabledHotkeys
if ($null -ne $disabled -and $disabled.Contains("E")) {
    $restored = $disabled.Replace("E", "")
    if ([String]::IsNullOrEmpty($restored)) {
        Remove-ItemProperty -Path $advanced -Name DisabledHotkeys -ErrorAction SilentlyContinue
    } else {
        Set-ItemProperty -Path $advanced -Name DisabledHotkeys -Type String -Value $restored
    }
}

Add-Type -TypeDefinition @"
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;

public static class APXReturnToHubKeyboardHook {
    private const int WhKeyboardLl = 13;
    private const int WmKeyDown = 0x0100;
    private const int WmSysKeyDown = 0x0104;
    private const int VirtualKeyE = 0x45;
    private const int VirtualKeyLeftWin = 0x5B;
    private const int VirtualKeyRightWin = 0x5C;

    private delegate IntPtr LowLevelKeyboardProc(int code, IntPtr message, IntPtr data);
    private static readonly LowLevelKeyboardProc Callback = HookCallback;
    private static IntPtr hook = IntPtr.Zero;
    private static bool rebootStarted;

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(
        int hookId, LowLevelKeyboardProc callback, IntPtr module, uint threadId);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool UnhookWindowsHookEx(IntPtr hookHandle);

    [DllImport("user32.dll")]
    private static extern IntPtr CallNextHookEx(
        IntPtr hookHandle, int code, IntPtr message, IntPtr data);

    [DllImport("user32.dll")]
    private static extern short GetAsyncKeyState(int virtualKey);

    [DllImport("user32.dll")]
    private static extern int GetMessage(
        out Message message, IntPtr window, uint minimum, uint maximum);

    [DllImport("user32.dll")]
    private static extern void PostQuitMessage(int exitCode);

    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr GetModuleHandle(string moduleName);

    [StructLayout(LayoutKind.Sequential)]
    private struct Point { public int X; public int Y; }

    [StructLayout(LayoutKind.Sequential)]
    private struct Message {
        public IntPtr Window;
        public uint Id;
        public UIntPtr WParam;
        public IntPtr LParam;
        public uint Time;
        public Point Cursor;
        public uint Private;
    }

    private static void Log(string text) {
        try {
            string directory = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "APX");
            Directory.CreateDirectory(directory);
            File.AppendAllText(Path.Combine(directory, "ReturnToHub.log"),
                DateTimeOffset.Now.ToString("o") + " " + text + Environment.NewLine);
        } catch { }
    }

    private static bool RebootToApx() {
        try {
            string shutdown = Environment.ExpandEnvironmentVariables(
                @"%WINDIR%\System32\shutdown.exe");
            Process.Start(new ProcessStartInfo {
                FileName = shutdown,
                Arguments = "/r /t 0 /d p:0:0 /c \"Regressar ao APX HUB\"",
                UseShellExecute = false,
                CreateNoWindow = true
            });
            Log("WIN+E accepted; APX reboot requested");
            PostQuitMessage(0);
            return true;
        } catch (Exception error) {
            Log("reboot failed: " + error.GetType().Name + ": " + error.Message);
            return false;
        }
    }

    private static IntPtr HookCallback(int code, IntPtr message, IntPtr data) {
        long kind = message.ToInt64();
        if (code >= 0 && (kind == WmKeyDown || kind == WmSysKeyDown) &&
                Marshal.ReadInt32(data) == VirtualKeyE) {
            bool windowsPressed = (GetAsyncKeyState(VirtualKeyLeftWin) & 0x8000) != 0 ||
                                  (GetAsyncKeyState(VirtualKeyRightWin) & 0x8000) != 0;
            if (windowsPressed && !rebootStarted) {
                rebootStarted = true;
                if (RebootToApx()) return new IntPtr(1);
                rebootStarted = false;
            }
        }
        return CallNextHookEx(hook, code, message, data);
    }

    public static int Run() {
        using (Process process = Process.GetCurrentProcess())
        using (ProcessModule module = process.MainModule) {
            hook = SetWindowsHookEx(WhKeyboardLl, Callback,
                GetModuleHandle(module.ModuleName), 0);
        }
        if (hook == IntPtr.Zero) {
            Log("keyboard hook failed; win32=" + Marshal.GetLastWin32Error());
            return 2;
        }
        Log("keyboard hook ready");
        try {
            Message message;
            while (GetMessage(out message, IntPtr.Zero, 0, 0) > 0) { }
            return 0;
        } finally {
            UnhookWindowsHookEx(hook);
            hook = IntPtr.Zero;
        }
    }
}
"@

[void][APXReturnToHubKeyboardHook]::Run()
